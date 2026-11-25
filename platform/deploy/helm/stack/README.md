# hc-stack: chart de Helm del stack de una empresa

Crea **todo lo que necesita una empresa** en su propio namespace: un servicio Django con su PostgreSQL por cada archivo de `services/`, el broker (NATS) y, según el ambiente, Mailpit, ingress, aislamiento de red y cuotas. El mismo chart sirve para `dev`, `testing` y `production`; solo cambia el archivo de valores.

> Probado con Helm 4.3 (`helm lint`, `helm template`) y validado contra el esquema de Kubernetes 1.35 con kubeconform: `make helm-check`. **No** se instaló en un clúster real: eso se hace en la fase 3, cuando exista el clúster de testing.

## Estructura

```
platform/deploy/helm/
├── check.sh                  # helm lint + helm template + kubeconform de los 3 ambientes
└── stack/
    ├── Chart.yaml
    ├── values.yaml           # valores por defecto (todos los servicios los heredan)
    ├── values-dev.yaml       # clúster local (k3d, kind, minikube)
    ├── values-testing.yaml   # VM de testing
    ├── values-production.yaml
    ├── services/             # UN ARCHIVO POR SERVICIO: lo edita su equipo
    │   ├── events.yaml  access.yaml  requests.yaml
    │   └── incidents.yaml  problems.yaml  knowledge.yaml
    └── templates/
        ├── app.yaml          # Deployment (+ initContainer de migraciones) y Service por servicio
        ├── configmap.yaml    # variables no secretas
        ├── secrets.yaml      # opcional (secrets.create)
        ├── db.yaml           # StatefulSet con PVC + Service headless por servicio
        ├── broker.yaml  mailpit.yaml  ingress.yaml
        ├── networkpolicy.yaml  quota.yaml
        └── _helpers.tpl  NOTES.txt
```

## Cómo se combinan los valores

De menor a mayor prioridad:

1. `defaults` de `values.yaml`: réplicas, recursos, sondas, seguridad, imagen de PostgreSQL...
2. `services/<nombre>.yaml`: lo que el equipo dueño declara de su servicio.
3. `serviceOverrides.<nombre>` de `values-<ambiente>.yaml`: ajuste de un servicio en un ambiente sin tocar el archivo del equipo.
4. `--set` de la línea de comandos.

Los mapas se combinan en profundidad: si `events.yaml` solo cambia `db.resources.limits.memory`, conserva el resto de `defaults`.

## Qué crea cada servicio

| Recurso | Nombre | Notas |
|---|---|---|
| Deployment | `<servicio>` | Sondas de arranque, vida y disponibilidad (`/health/live`, `/health/ready`), `resources`, usuario no root |
| initContainer `migrate` | | Corre `manage.py migrate` antes de arrancar; reintenta hasta que la BD responda. Se desactiva con `migrate: false` |
| Service | `<servicio>` | ClusterIP en el puerto del servicio |
| ConfigMap | `<servicio>-config` | `SERVICE_NAME`, `PORT`, `DEBUG`, `LOG_LEVEL`, `ALLOWED_HOSTS`, `WEB_CONCURRENCY`, `TENANT_ID`, `EMPRESA_ID`, `BROKER_URL`, `EMAIL_HOST`, `EMAIL_PORT` y el `env` del servicio |
| Secret (referencia) | `<servicio>-secret` | Claves `SECRET_KEY` y `POSTGRES_PASSWORD`; `DATABASE_URL` se arma en el pod |
| StatefulSet + PVC | `<servicio>-db` | Una PostgreSQL por servicio, con volumen propio |
| Service headless | `<servicio>-db` | La app se conecta a `<servicio>-db:5432` |

Además, una vez por stack: `broker` (NATS con JetStream), `mailpit` (solo dev y testing), `Ingress`, `NetworkPolicy`, `ResourceQuota` y `LimitRange`.

## Instalar un stack

```bash
helm upgrade --install empresa-demo platform/deploy/helm/stack \
  -n empresa-demo --create-namespace \
  -f platform/deploy/helm/stack/values-testing.yaml \
  --set global.tenantId=empresa-demo \
  --set global.imageTag="$(git rev-parse HEAD)"
kubectl -n empresa-demo get pods
```

- Convención: **namespace = nombre del release = `global.tenantId`**.
- `global.imageTag` es obligatorio: usa el SHA del commit (etiqueta inmutable). El chart se niega a renderizar sin él.
- Quitar el stack: `helm uninstall empresa-demo -n empresa-demo`. Los PVC y los Secret **se conservan** a propósito (para no perder datos); `kubectl delete ns empresa-demo` los borra.

## Cómo agregar un servicio al stack

1. **Copia** el archivo de un servicio parecido: `cp services/requests.yaml services/<nuevo>.yaml`.
2. **Edita** el archivo nuevo (el nombre del archivo y `name` deben coincidir; el chart lo comprueba):

   | Clave | Qué poner |
   |---|---|
   | `name` | Nombre del servicio, igual que el archivo (`incidents`) |
   | `port` | El mismo `PORT` del servicio (Makefile y `.env.example`) |
   | `image.repository` | `hc-<servicio>`; el registro y la etiqueta salen de `global` |
   | `ingress.path` | Prefijo público, p. ej. `/api/incidents`. Déjalo vacío para no publicarlo |
   | `env` | Variables propias (se guardan como texto). Las secretas **no** van aquí |
   | `db.image` | Solo si no usas `postgres:16-alpine` (Eventos usa TimescaleDB) |
   | `resources`, `db.resources`, `db.storage` | Solo si necesitas más que los valores por defecto |
   | `migrate: false` | Si el servicio no usa `manage.py migrate` |
   | `db.enabled: false` | Si el servicio no tiene base de datos |

3. **Cumple el contrato del chart**: el contenedor lee `PORT`, `SECRET_KEY` y `DATABASE_URL` del entorno, expone `/health/live` y `/health/ready` y corre con el UID 10001 (así lo hace la plantilla de `platform/templates/django-service`).
4. **Dueño del archivo**: agrega su línea a `.github/CODEOWNERS` (ver más abajo).
5. **Valida**: `make helm-check` desde la raíz del repositorio.
6. **PR** a `develop` con el título `feat(deploy): agrega <servicio> al stack`, y menciona a Plataforma.

Para quitar un servicio de un solo ambiente sin borrar su archivo: `serviceOverrides.<nombre>.enabled: false` en el `values-<ambiente>.yaml`.

## Secretos

Cada servicio necesita `<servicio>-secret` con `SECRET_KEY` y `POSTGRES_PASSWORD`.

- **dev y testing:** `secrets.create: true` los genera aleatorios al instalar y los conserva en cada `helm upgrade`.
- **producción:** `secrets.create: false`; el aprovisionador los crea **antes** de instalar el chart. Usa solo hexadecimal para que la contraseña viaje sin problemas dentro de la URL de la BD:

  ```bash
  NS=empresa-12
  for s in events access requests incidents problems knowledge; do
    kubectl -n "$NS" create secret generic "$s-secret" \
      --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
      --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 24)"
  done
  ```

Sin el Secret, los pods quedan en `CreateContainerConfigError` hasta que exista.

## Ambientes

| | `dev` | `testing` | `production` |
|---|---|---|---|
| Etiqueta de imagen | `dev` | `develop` (Jenkins pone el SHA) | obligatoria (`--set`) |
| Secretos | los crea el chart | los crea el chart | los crea el aprovisionador |
| Mailpit | sí | sí | no (SMTP real) |
| Ingress | no | sí (`traefik`) | sí, con TLS (cert-manager) |
| Broker con volumen | no | no | sí |
| NetworkPolicy y cuotas | no | no | sí |
| Almacenamiento de cada BD | 512Mi | 1Gi | 5Gi |

## Cuánto ocupa un stack (con los valores por defecto)

Calculado sobre el chart renderizado, sin contar el sistema ni otros stacks:

| Ambiente | Pods | Memoria (requests / límites) | CPU (requests / límites) |
|---|---|---|---|
| testing | 14 | 1.69 GiB / 3.44 GiB | 0.68 / 6.50 |
| production | 13 | 1.66 GiB / 3.38 GiB | 0.65 / 6.25 |

Los `requests` son los que el planificador reserva: dividen la capacidad de la VM entre las empresas. Ajústalos con el consumo real (`kubectl top pods`) antes de la fase 4.

## Validar en CI

```bash
make helm-check
```

Ejecuta, para `dev`, `testing` y `production`: `helm lint`, `helm template` y, si está instalado, `kubeconform` contra el esquema de Kubernetes. `Jenkinsfile` (en esta carpeta) lo corre cuando cambia algo de `platform/deploy/helm/`. Requiere `helm` en el agente de Jenkins.

## CODEOWNERS

Plataforma es dueña del chart y cada equipo de su propio archivo (en `CODEOWNERS` gana la última regla que coincide, así que estas líneas van **al final**):

```
/platform/deploy/                                          @<org>/team-platform
/platform/deploy/helm/stack/services/events.yaml           @<org>/team-events
/platform/deploy/helm/stack/services/access.yaml           @<org>/team-access
/platform/deploy/helm/stack/services/requests.yaml         @<org>/team-requests
/platform/deploy/helm/stack/services/incidents.yaml        @<org>/team-incidents
/platform/deploy/helm/stack/services/problems.yaml         @<org>/team-problems
/platform/deploy/helm/stack/services/knowledge.yaml        @<org>/team-problems
```

## Fuera de este chart

- **El frontend** es global (una sola instalación para todas las empresas) y se despliega aparte. Aquí solo se enruta: si defines `frontend.externalName`, el ingress de la empresa sirve `/` hacia él.
- **El gateway y el directorio de empresas** son globales y tampoco van por empresa.
- **Respaldos** (`pg_dump` en un CronJob), **HPA** y **cert-manager** llegan en la fase 3.
- La imagen de Eventos (`timescale/timescaledb:latest-pg16`) es mutable: fija una versión concreta cuando se decida.
