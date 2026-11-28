
# Runbook de despliegue y acceso a testing

## Objetivo

Esta guía explica cómo acceder al entorno testing de Help Chair, desplegar servicios, revisar su estado, consultar logs y regresar a una versión anterior si ocurre algún problema.

La intención es que cualquier integrante autorizado pueda seguir el procedimiento sin depender de una sola persona.

Relacionado con el Issue #101 de Plataforma de Deployment.

## 1. Antes de comenzar

El entorno testing utiliza una máquina virtual de Google Cloud con Kubernetes (k3s).

Para trabajar se necesita:

- Tener acceso autorizado al proyecto de Google Cloud.
- Tener instalados gcloud, kubectl y Helm.
- Contar con el kubeconfig correspondiente.
- Tener una copia actualizada del repositorio.
- Conocer el namespace donde se hará el despliegue.

Los accesos deben solicitarse al equipo de Plataforma. No deben compartirse contraseñas, tokens ni archivos kubeconfig dentro del repositorio.

## 2. Acceso al clúster

Primero hay que iniciar sesión en Google Cloud:

```bash
gcloud auth login
```

Para conectarse a la API de Kubernetes se utiliza un túnel IAP:

```bash
gcloud compute start-iap-tunnel hc-testing 6443 --local-host-port=localhost:6443 --zone us-central1-a
```

El túnel debe permanecer abierto mientras se utiliza kubectl.

En otra terminal se configura el kubeconfig que haya proporcionado Plataforma:

```bash
export KUBECONFIG=/ruta/al/kubeconfig-requests.yaml
```

Se puede comprobar el acceso con:

```bash
kubectl get namespaces
kubectl get pods -A
```

Los integrantes con permisos de solo lectura pueden consultar recursos y logs. Para desplegar o revertir cambios se necesitan permisos adicionales.

## 3. Validación antes de desplegar

Desde la raíz del repositorio se ejecuta:

```bash
make helm-check
```

Este comando revisa los charts de Helm para los ambientes dev, testing y production.

Antes de desplegar también se debe confirmar que la imagen correspondiente ya esté publicada y disponible en GHCR.

No se debe continuar si la validación falla.

## 4. Despliegue en testing

El chart principal está ubicado en:

`platform/deploy/helm/stack/`

El archivo de valores del ambiente es:

`platform/deploy/helm/stack/values-testing.yaml`

Para instalar o actualizar un stack de ejemplo:

```bash
helm upgrade --install empresa-demo platform/deploy/helm/stack \
  -n empresa-demo --create-namespace \
  -f platform/deploy/helm/stack/values-testing.yaml \
  --set global.tenantId=empresa-demo \
  --set global.imageTag="<SHA_PUBLICADO>"
```

Se debe sustituir SHA_PUBLICADO por el identificador de una imagen realmente publicada en GHCR.

Este comando requiere permisos de despliegue y no debe ejecutarse sobre un entorno compartido sin autorización.

## 5. Verificar el despliegue

Después de desplegar, revisar los recursos:

```bash
kubectl -n empresa-demo get pods
kubectl -n empresa-demo get services
kubectl -n empresa-demo get ingress
```

Comprobar también los recursos utilizados:

```bash
kubectl -n empresa-demo top pods
```

Si algún pod no inicia, consultar su descripción:

```bash
kubectl -n empresa-demo describe pod <nombre-del-pod>
```

El despliegue se considera listo para pruebas funcionales cuando los servicios necesarios están disponibles y responden correctamente.

## 6. Consultar logs

Para revisar los logs de un pod:

```bash
kubectl -n empresa-demo logs <nombre-del-pod>
```

Para seguir los logs mientras el servicio funciona:

```bash
kubectl -n empresa-demo logs -f <nombre-del-pod>
```

Si el pod tiene varios contenedores, se debe indicar el contenedor correspondiente con la opción `-c`.

Antes de reportar un error conviene registrar el servicio afectado, la fecha, el mensaje encontrado y los pasos que lo provocaron.

No incluir contraseñas ni tokens en las evidencias.

## 7. Revertir un despliegue

Si una actualización provoca problemas, primero revisar el historial:

```bash
helm history empresa-demo -n empresa-demo
```

Para regresar a una revisión anterior:

```bash
helm rollback empresa-demo <revision> -n empresa-demo
```

Después comprobar nuevamente los pods:

```bash
kubectl -n empresa-demo get pods
```

La revisión debe elegirse a partir del historial real de Helm.

Un rollback de Helm no garantiza revertir cambios de base de datos. Si hubo migraciones, se debe revisar el procedimiento de recuperación antes de ejecutarlo.

## 8. Encendido y apagado de testing

Plataforma cuenta con comandos para controlar la máquina virtual y reducir costos.

Desde la raíz del repositorio:

Para apagar:

```bash
make testing-down
```

Para encender:

```bash
make testing-up
```

Estos comandos requieren permisos sobre la máquina virtual de Google Cloud.

Después de encender, se debe restablecer el túnel IAP y comprobar que el nodo y los servicios estén disponibles.

No apagar testing mientras otro equipo esté realizando pruebas sin avisarle primero.

## 9. Problemas frecuentes

### No hay conexión con Kubernetes

Verificar que la máquina virtual esté encendida, que el túnel IAP siga activo y que KUBECONFIG apunte al archivo correcto.

### Los pods no inician

Consultar `kubectl describe pod` y los logs. Revisar errores de imágenes, configuración, secretos y recursos disponibles.

### La imagen no se descarga

Confirmar que la etiqueta exista en GHCR y que el clúster tenga permisos para descargarla.

### El servicio no responde

Comprobar el estado de los pods, el Service, el Ingress y los logs de la aplicación.

### Una actualización falla

Revisar el historial con `helm history` y coordinar un rollback si es necesario.

## 10. Registro de pruebas

Cada prueba de despliegue debe registrar:

- Fecha de ejecución.
- Persona que realizó la prueba.
- Namespace utilizado.
- SHA de la imagen desplegada.
- Comandos ejecutados.
- Resultado obtenido.
- Problemas encontrados y solución aplicada.

La evidencia puede incluir resultados de terminal, capturas o enlaces a los registros correspondientes.

## 11. Validación del runbook

Antes de considerar completa esta guía, una persona de otro equipo deberá seguirla en el entorno autorizado.

Se debe comprobar que puede acceder al clúster y realizar o verificar un despliegue o rollback, según sus permisos.

El resultado se registrará en el Issue #101.

## Referencias

- `platform/deploy/README.md`
- `platform/deploy/cluster/README.md`
- `platform/deploy/helm/stack/README.md`
- `docs/runbooks/jenkins.md`

Este documento reúne los procedimientos existentes. Su ejecución completa en el entorno real de testing queda sujeta a la disponibilidad del clúster y los permisos correspondientes.
