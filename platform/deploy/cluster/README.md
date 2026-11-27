# Clúster de testing (k3s en una VM de Google Cloud)

Runbook del clúster donde se despliega el ambiente de **testing** (fase 3) y se ensaya producción (fase 4). Cumple los criterios de aceptación de la tarea de clúster; cada uno tiene su comprobación en la sección 6.

> **Estado:** los scripts están revisados con ShellCheck y ensayados con `DRY_RUN=1`; el manifiesto de RBAC está validado contra el esquema de Kubernetes. **No se ejecutaron contra una cuenta de Google Cloud**: eso lo hace Plataforma al crear la VM (pasos de la sección 4). Registra en el PR el resultado de la sección 6.

## 0. Quién ejecuta qué, y dónde

**Todo se ejecuta desde tu computadora**, dentro de tu clon de `help-chair` (con `gcloud` y `kubectl` instalados y `gcloud auth login` hecho). **Solo un script corre dentro de la VM** (`10-install-k3s.sh`) y tú lo envías con `gcloud`: **no hace falta clonar el repositorio en la VM**. Jenkins no ejecuta ninguno de estos scripts: solo valida el chart y el compose.

```
TU COMPUTADORA (clon del repo + gcloud + kubectl)                  VM DE GOOGLE CLOUD (hc-testing)
─────────────────────────────────────────────────                  ─────────────────────────────────
00-gcp-create-vm.sh ──── gcloud ───────────────────────────────▶   (se CREA la VM, su IP y el firewall)
gcloud compute scp 10-install-k3s.sh ──────────────────────────▶   ~/10-install-k3s.sh
gcloud compute ssh ... 'bash 10-install-k3s.sh' ───────────────▶   EJECUTA 10-install-k3s.sh → instala k3s
11-fetch-admin-kubeconfig.sh ◀──────────────────────────────────   /etc/rancher/k3s/k3s.yaml
gcloud compute start-iap-tunnel ◀═══════ túnel ═══════════════▶   API de Kubernetes (puerto 6443)
20, 30, 31 y 40 ──── kubectl, por el túnel ────────────────────▶   el clúster
make testing-down / testing-up ──── gcloud ────────────────────▶   se APAGA / ENCIENDE la VM
```

| Script | Dónde corre | Quién | Cuándo | Qué hace |
|---|---|---|---|---|
| `00-gcp-create-vm.sh` | Tu computadora | Plataforma | **Una vez, antes de que exista la VM**: él la crea | Reserva la IP estática, abre el firewall (HTTP, HTTPS y el túnel IAP) y crea la VM con Ubuntu 24.04 |
| `10-install-k3s.sh` | **Dentro de la VM** (enviado con `scp`) | Plataforma | Una vez, justo después del 00 | Instala k3s con los Secret cifrados y espera a que el nodo esté Ready |
| `11-fetch-admin-kubeconfig.sh` | Tu computadora | Plataforma | Una vez (y si cambia la IP) | Baja el kubeconfig de administrador a `kubeconfig-admin.yaml` |
| `20-install-addons.sh` | Tu computadora (kubeconfig admin + túnel abierto) | Plataforma | Una vez | Verifica el ingress (Traefik) y metrics-server |
| `30-rbac-readonly.sh` | Tu computadora (ídem) | Plataforma | Una vez, y al sumar un equipo | Crea una cuenta de solo lectura por equipo |
| `31-make-kubeconfig.sh <equipo>` | Tu computadora (ídem) | Plataforma | Una vez por equipo; renovar cada 30 días | Genera `kubeconfig-<equipo>.yaml` con un token que caduca |
| `40-verify-networkpolicy.sh` | Tu computadora (ídem) | Plataforma | Una vez; repetir si cambian k3s o el CNI | Prueba que las `NetworkPolicy` se aplican |
| `50-cluster-down.sh` / `51-cluster-up.sh` | Tu computadora | Plataforma | Cada día (`make testing-down` / `testing-up`) | Apaga y enciende la VM |

### Cómo funciona cada pieza por dentro

- **`lib.sh`** no se ejecuta solo: los demás lo cargan. Define `run` (que ejecuta un comando, o solo lo imprime si `DRY_RUN=1`), `need` (comprueba que exista `gcloud` o `kubectl`) y los valores por defecto de la VM (`hc-testing`, zona `us-central1-a`).
- **`00`** es **idempotente**: antes de crear la IP, el firewall o la VM, pregunta con `describe` si ya existen, así que puedes repetirlo sin duplicar nada. Con `DRY_RUN=1` te muestra los comandos de `gcloud` sin ejecutarlos: **empieza siempre con un ensayo**.
- **`10`** descarga el instalador oficial de k3s y le pasa las opciones (`--tls-san` con la IP, `--secrets-encryption`). No desactiva el controlador de `NetworkPolicy` ni metrics-server, que k3s trae.
- **`11`** copia por SSH el archivo `k3s.yaml` de la VM y cambia `127.0.0.1` por la dirección con la que llegarás a la API.
- **`30` y `31`** usan el rol `view` que ya trae Kubernetes: `30` crea las cuentas y `31` pide a Kubernetes un token con caducidad y arma el kubeconfig del equipo.
- **`40`** crea dos namespaces de prueba, un servidor en uno, aplica una política y comprueba que el otro namespace queda bloqueado; limpia todo al terminar.

### Primera vez: lista de verificación

1. `gcloud auth login` y un proyecto con el crédito activo.
2. `DRY_RUN=1 PROJECT_ID=<proyecto> ./00-gcp-create-vm.sh` y revisa lo que imprime.
3. Ejecuta el 00 real, luego el 10 dentro de la VM, y sigue con la sección 4.

## 1. Decisión: una VM con k3s, no GKE

Es la propuesta del ADR-87 (D-19). Se confirma con estas razones:

| | VM + k3s (elegida) | GKE |
|---|---|---|
| Costo mientras se usa | El de la VM (e2-standard-2 ≈ 49 USD/mes si estuviera encendida 24×7; e2-standard-4, aproximadamente el doble) | VM(s) de los nodos **más** la tarifa de administración del clúster |
| Apagar para ahorrar | **Se detiene la VM**: solo cuesta el disco y la IP estática. Un comando (`make testing-down`) | No se puede apagar el plano de control; hay que reducir los nodos a cero o escalar los pods, y la tarifa del clúster sigue |
| Operación | La administramos nosotros (actualizar k3s, respaldar el disco) | Google administra el plano de control y las actualizaciones |
| `NetworkPolicy` | k3s trae un controlador integrado (kube-router), activo por defecto | Requiere activarlo (Dataplane V2 o Calico) |
| Fase 4 (muchos stacks) | Se redimensiona la VM o se agrega un nodo | Se agregan nodos fácilmente |
| Complejidad para 5 semanas | Baja: un nodo, un script | Mayor: red, IAM, nodepools, cuotas |

**Cuándo reconsiderarlo:** si la VM se queda corta en la fase 4 y hace falta más de un nodo, o si el equipo prefiere no operar el servidor. El chart y los manifiestos son los mismos; solo cambia cómo se crea el clúster.

Verifica los precios actuales en la calculadora de Google Cloud antes de decidir el tamaño: son aproximados y cambian con la región.

### Tamaño de la VM

Un stack completo ocupa, según el chart renderizado (`platform/deploy/helm/stack/README.md`):

| | Memoria (requests / límites) | CPU (requests / límites) |
|---|---|---|
| 1 stack de testing | 1.69 GiB / 3.44 GiB | 0.68 / 6.50 |

El planificador reserva los **requests**. Descontando unos 0.6 CPU y 1.5 GiB para k3s, Traefik, CoreDNS y metrics-server (estimación: mídela con `kubectl top`), caben aproximadamente:

| VM | Stacks por CPU (requests) | Stacks por memoria (requests) |
|---|---|---|
| e2-standard-2 (2 vCPU, 8 GiB) | ~2 | ~3 |
| e2-standard-4 (4 vCPU, 16 GiB) | ~5 | ~8 |

**Recomendación:** empezar con **e2-standard-4** (valor por defecto del script): la fase 4 necesita varias empresas y el crédito de 300 USD alcanza, sobre todo si se apaga fuera de horario. Si el crédito preocupa, e2-standard-2 sirve para el stack único de testing de la fase 3 y se redimensiona después (sección 8). Disco de 60 GB: cada base de datos reserva 1 a 5 GiB.

## 2. Ingress: Traefik por defecto (ingress-nginx está retirado)

El proyecto Kubernetes retiró **ingress-nginx en marzo de 2026**: ya no hay versiones, correcciones de errores ni parches de seguridad ([anuncio](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/), [comunicado de enero de 2026](https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/)). El plan y la tarea de clúster lo nombran porque se escribieron antes.

Una VM expuesta a internet no debería ejecutar un componente sin parches de seguridad, así que **los scripts usan Traefik, que viene con k3s** (no hay nada que instalar y se mantiene). Todo es compatible:

- Las plantillas de Helm usan el recurso estándar `Ingress` con `ingressClassName` configurable (`ingress.className: traefik`), sin anotaciones propias de un controlador.
- cert-manager (fase 3) funciona igual con cualquiera.

Si el equipo quiere cumplir el texto de la tarea al pie de la letra: `INGRESS_CONTROLLER=nginx` en `10-install-k3s.sh` y `20-install-addons.sh` (exige aceptar el riesgo con `ACCEPT_RETIRED_INGRESS_NGINX=yes`), y `ingress.className: nginx` y `networkPolicy.ingressControllerNamespace: ingress-nginx` en los valores. **Sugerencia:** cambiar el criterio de la tarea a «controlador de ingress mantenido (Traefik de k3s)» y anotarlo en `docs/DECISIONS.md`.

## 3. Requisitos

- Cuenta de Google Cloud con el crédito activo y la facturación habilitada; `gcloud` instalado y autenticado (`gcloud auth login`).
- `kubectl` y, opcionalmente, `helm` en tu máquina.
- Quién tiene acceso: **administración, solo Plataforma**; los demás equipos, solo lectura.

## 4. Paso a paso

Todos los scripts están en `platform/deploy/cluster/scripts/` y aceptan `DRY_RUN=1` para ver qué harían.

```bash
cd platform/deploy/cluster/scripts

# 4.1 Crear la VM, la IP estática y el firewall
DRY_RUN=1 PROJECT_ID=<tu-proyecto> ./00-gcp-create-vm.sh     # ensayo: solo imprime
PROJECT_ID=<tu-proyecto> ./00-gcp-create-vm.sh               # real; al final muestra la IP pública

# 4.2 Instalar k3s dentro de la VM (el script anterior imprime estos comandos con tu IP)
gcloud compute scp 10-install-k3s.sh hc-testing:~ --zone us-central1-a
gcloud compute ssh hc-testing --zone us-central1-a --command 'TLS_SAN=<IP> bash 10-install-k3s.sh'

# 4.3 Kubeconfig de administrador (solo Plataforma) y verificación
SERVER_HOST=127.0.0.1 ./11-fetch-admin-kubeconfig.sh         # se usa con el túnel IAP de 4.4
export KUBECONFIG=$PWD/kubeconfig-admin.yaml

# 4.4 Túnel IAP hacia la API (déjalo abierto en otra terminal)
gcloud compute start-iap-tunnel hc-testing 6443 --local-host-port=localhost:6443 --zone us-central1-a
kubectl get nodes                                            # el nodo debe estar Ready

# 4.5 Ingress y metrics-server
./20-install-addons.sh

# 4.6 Cuentas de solo lectura y kubeconfig de cada equipo
./30-rbac-readonly.sh
for t in events access requests incidents problems-kb frontend; do ./31-make-kubeconfig.sh $t; done

# 4.7 ¿El CNI aplica NetworkPolicy?
./40-verify-networkpolicy.sh
```

Si SSH directo no responde, agrega `--tunnel-through-iap` a los comandos `gcloud compute ssh/scp`.

### Acceso de los equipos a la API

La API (6443) **no se abre a internet**. Cada integrante entra por el túnel IAP de Google:

1. Plataforma le da el rol **IAP-secured Tunnel User** (`roles/iap.tunnelResourceAccessor`) en el proyecto o en la VM:
   `gcloud projects add-iam-policy-binding <proyecto> --member=user:<correo> --role=roles/iap.tunnelResourceAccessor`
2. El integrante instala `gcloud`, ejecuta el comando del paso 4.4 y usa su `kubeconfig-<equipo>.yaml`. Si `gcloud` pide un permiso adicional (por ejemplo `roles/compute.viewer` para resolver el nombre de la VM), agrégalo: no hace falta ningún rol de acceso a la VM.

**No les des acceso SSH a la VM**: con él serían administradores del clúster y el kubeconfig «de solo lectura» no serviría de nada. El túnel IAP solo da acceso al puerto de la API. (Alternativa menos segura: `API_CIDR=<ip>/32` en el paso 4.1 abre el puerto a una IP concreta; las IP de casa cambian, así que no la recomendamos.)

El firewall por defecto de Google Cloud suele incluir una regla que abre SSH a todo internet; revísala (`gcloud compute firewall-rules list`) y restringe o borra la que no uses.

## 5. Permisos: qué puede cada quien

| Quién | Credencial | Puede |
|---|---|---|
| Plataforma | `kubeconfig-admin.yaml` | Todo. No se comparte ni se sube al repositorio |
| Cada equipo (6) | `kubeconfig-<equipo>.yaml` (token de 30 días) | Ver recursos y leer logs de **todos** los namespaces (rol `view`) y `kubectl top` |
| Cada equipo | | **No** puede: modificar ni borrar, leer Secrets, abrir una terminal en un pod ni reenviar puertos |

- Los tokens caducan: para renovar, `./31-make-kubeconfig.sh <equipo>` (con `DURATION=` para cambiar la vigencia).
- Entrega los kubeconfig por un canal privado: son credenciales. Los archivos `kubeconfig-*.yaml` están en `.gitignore`.
- Los equipos pueden leer los ConfigMap de todas las empresas (variables no secretas). Si en la fase 4 eso no es aceptable, se cambia `view` por un rol limitado a `testing`.
- Plataforma también debería trabajar a diario con una cuenta de solo lectura y reservar la de administrador para cambios.
- k3s cifra los Secret en disco (`--secrets-encryption`).

## 6. Criterios de aceptación y cómo comprobarlos

| Criterio | Comprobación |
|---|---|
| `kubectl get nodes` funciona con los nodos Ready | `kubectl get nodes` → `Ready` |
| Ingress y metrics-server instalados | `./20-install-addons.sh` termina sin errores; `kubectl get ingressclass`; `kubectl top nodes` muestra CPU y memoria |
| Kubeconfig de solo lectura por equipo; administración solo para Plataforma | `kubectl --kubeconfig kubeconfig-events.yaml auth can-i get pods -A` → `yes`; `... auth can-i delete pods -A` → `no`; `... auth can-i get secrets -A` → `no` |
| Verificado que el CNI aplica `NetworkPolicy` | `./40-verify-networkpolicy.sh` → tres `PASS` y «OK: el CNI aplica NetworkPolicy» |
| Procedimiento de apagado y encendido | Sección 7: `make testing-down` y `make testing-up`; registra el tiempo y que los pods vuelven |

Pega la salida de estas comprobaciones en la descripción del PR.

## 7. Apagado y encendido (control de costos)

```bash
make testing-down        # apaga la VM (ordenado: PostgreSQL recibe SIGTERM)
make testing-up          # la enciende; con KUBECONFIG definido espera a que el nodo esté Ready
```

- Apagada, la VM solo cuesta el **disco** y la **IP estática** (unos centavos por hora: revisa la calculadora). Los datos de los stacks (PVC) quedan en el disco.
- Al encender, los pods vuelven solos; las bases de datos tardan un poco más. `51-cluster-up.sh` lista los pods que aún no están `Running`.
- Con el túnel IAP, abre el túnel de nuevo después de encender.
- **Apagado automático (opcional):** Google Cloud permite programar encendido y apagado. Verifica los parámetros con `gcloud compute resource-policies create instance-schedule --help`:

  ```bash
  gcloud compute resource-policies create instance-schedule hc-horario \
    --region us-central1 --timezone America/Mexico_City \
    --vm-start-schedule "0 8 * * 1-5" --vm-stop-schedule "0 22 * * 1-5"
  gcloud compute instances add-resource-policies hc-testing \
    --resource-policies hc-horario --zone us-central1-a
  ```

- Mide el gasto en **Facturación → Informes** de Google Cloud y crea una alerta de presupuesto.

## 8. Redimensionar la VM

```bash
make testing-down
gcloud compute instances set-machine-type hc-testing --zone us-central1-a --machine-type e2-standard-4
make testing-up
```

La IP, el disco y los datos se conservan.

## 9. Solución de problemas

| Síntoma | Qué hacer |
|---|---|
| `kubectl` no conecta | ¿Está abierto el túnel IAP? ¿`KUBECONFIG` apunta al archivo correcto? ¿La VM está encendida? |
| `x509: certificate is valid for ... not ...` | k3s se instaló sin `--tls-san` para ese nombre o IP. Con túnel IAP usa `127.0.0.1` |
| Nodo `NotReady` tras encender | `gcloud compute ssh hc-testing --zone us-central1-a --command 'sudo journalctl -u k3s -n 50'` |
| `kubectl top` dice «Metrics API not available» | Espera 1 o 2 minutos tras instalar; revisa `kubectl -n kube-system get pods` |
| `40-verify-networkpolicy.sh` falla | k3s se instaló con `--disable-network-policy`, o se cambió el CNI. Reinstala con el script 10 |
| Pods en `Pending` | `kubectl describe pod`: falta CPU/memoria (ver la tabla de tamaño) o PVC sin clase de almacenamiento |
| No se pueden descargar imágenes | ¿Son privadas en GHCR? Crea un `imagePullSecret` y usa `global.imagePullSecrets` |
