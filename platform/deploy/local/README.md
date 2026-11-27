# Entorno local (compose)

Un stack completo de Help Chair en tu máquina, igual para todo el equipo: 6 servicios Django, una PostgreSQL por servicio (Eventos usa TimescaleDB), la BD de Plataforma, el broker NATS, Mailpit y el frontend. Se levanta con **Podman sin privilegios de root** (probado el formato con `podman-compose 1.6.0`, el de Fedora 44).

```bash
make up        # construye las imágenes y levanta todo
make health    # consulta /health/ready de los 6 servicios (200 = listo)
make logs S=events
make down      # detiene (conserva los datos)
make reset     # borra contenedores Y datos y levanta de nuevo (pide confirmación)
```

La primera vez tarda varios minutos (construye 7 imágenes). Los servicios esperan a que su base de datos esté sana y aplican las migraciones al arrancar.

## Qué se levanta

Todo se publica solo en `127.0.0.1` (las BD llevan claves de desarrollo: no deben verse desde la red de la escuela).

| Servicio | URL / puerto | Base de datos (puerto) |
|---|---|---|
| events | http://127.0.0.1:8001 | `events-db` TimescaleDB (5441) |
| access | http://127.0.0.1:8002 | `access-db` (5442) |
| requests | http://127.0.0.1:8003 | `requests-db` (5443) |
| incidents | http://127.0.0.1:8004 | `incidents-db` (5444) |
| problems | http://127.0.0.1:8005 | `problems-db` (5445) |
| knowledge | http://127.0.0.1:8006 | `knowledge-db` (5446) |
| Plataforma (directorio de empresas) | el gateway aún no tiene contenedor | `gateway-db` (5447) |
| frontend | http://127.0.0.1:8080 | |
| Mailpit (correos de prueba) | http://127.0.0.1:8025 (web) · `mailpit:1025` (SMTP) | |
| broker (NATS, con JetStream) | `nats://127.0.0.1:4222` · monitor http://127.0.0.1:8222 | |

Conectarte a una base de datos desde tu máquina: `psql postgresql://events:events@127.0.0.1:5441/events` (usuario, clave y base llevan el nombre del servicio).

## Límites de recursos

Cada contenedor tiene límites de CPU y memoria (`deploy.resources.limits`), para que el stack quepa en una laptop:

| Componente | Memoria | CPU |
|---|---|---|
| Servicio Django (×6) | 256 MB | 0.50 |
| PostgreSQL (×6: access, requests, incidents, problems, knowledge, gateway) | 256 MB | 0.50 |
| TimescaleDB (events-db) | 512 MB | 0.50 |
| Broker NATS | 128 MB | 0.25 |
| Mailpit | 64 MB | 0.25 |
| Frontend | 64 MB | 0.25 |

Si todo llegara a su límite a la vez serían unos **3.8 GB**; en uso normal es bastante menos. Las PostgreSQL arrancan con `shared_buffers=64MB` y `max_connections=50` para caber en su límite.

### Límites de CPU sin root (Fedora)

Podman sin root solo aplica límites de CPU si systemd le delegó ese control. Compruébalo:

```bash
cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers
```

Debe incluir `cpu` (en Fedora 44 aparece `cpu io memory pids`). Si falta, se habilita una sola vez:

```bash
sudo mkdir -p /etc/systemd/system/user@.service.d
printf '[Service]\nDelegate=cpu cpuset io memory pids\n' | sudo tee /etc/systemd/system/user@.service.d/delegate.conf
sudo systemctl daemon-reload      # y cierra sesión y vuelve a entrar
```

## Comandos

| Comando | Qué hace |
|---|---|
| `make up` | Construye y levanta todo en segundo plano |
| `make down` | Detiene y quita los contenedores; **los datos se conservan** (volúmenes con nombre) |
| `make logs S=<servicio>` | Sigue los logs; sin `S`, de todos |
| `make ps` | Estado de los contenedores |
| `make build` | Reconstruye las imágenes sin levantar |
| `make health` | Código HTTP de `/health/ready` de cada servicio |
| `make reset` | **Borra los datos** y levanta de cero; pide escribir `si` (`YES=1` omite la pregunta) |
| `make compose-check` | Valida `compose.yaml` y los manifiestos del plan B (lo ejecuta también Jenkins) |

Los volúmenes se llaman `help-chair_<servicio>-data` (`podman volume ls`). El proyecto se llama `help-chair` gracias a `name:` en el compose; sin eso Podman lo llamaría `local` por el nombre de la carpeta.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `address already in use` | Otro programa usa el puerto (`ss -ltnp \| grep 8001`). Ciérralo, o cambia el puerto a la izquierda del `:` en `compose.yaml` |
| Un servicio queda `unhealthy` o reinicia | `make logs S=<servicio>`. Casi siempre es la BD o una migración con error |
| Un contenedor muere sin mensaje | Falta memoria: `podman inspect --format '{{.State.OOMKilled}}' <contenedor>` (`true` = superó su límite) |
| Cambié una migración que ya se había aplicado | `make reset` (las bases de datos quedan inconsistentes) |
| Podman pregunta de qué registro descargar una imagen | Las imágenes ya llevan `docker.io/`; si es de otro archivo, usa el nombre completo |
| Mailpit aparece `unhealthy` | Su comprobación (`/mailpit readyz`) requiere una versión reciente: `podman pull docker.io/axllent/mailpit:latest`. No afecta a los demás |
| Avisos de «external compose provider» | Los oculta el Makefile (`PODMAN_COMPOSE_WARNING_LOGS=false`) |
| `Error: short-name resolution` | Falta el prefijo `docker.io/` en alguna imagen que agregaste |

## Plan B: `podman kube play`

Si `podman compose` falla (por ejemplo, por la versión del proveedor), el entorno se levanta con manifiestos de Kubernetes que Podman ejecuta directamente. Están en `platform/deploy/local/kube/`.

```bash
make kube-build     # construye las imágenes (los manifiestos usan imagePullPolicy: Never)
make kube-up        # podman kube play de cada manifiesto
podman pod ps       # un pod por servicio, con su base de datos dentro
make kube-down      # detiene (conserva los datos)
make kube-reset     # borra también los datos
```

- Cada servicio es un **pod con dos contenedores** (la app y su PostgreSQL); dentro del pod se ven por `127.0.0.1`. Los puertos y los límites son los mismos que en el compose.
- **Limitación:** los pods no se resuelven entre sí por nombre en la red por defecto. Sirve para trabajar en un servicio con su base de datos; para integrar servicios entre sí usa el compose.
- Los manifiestos se **generan**; no los edites a mano: cambia las tablas de `kube/generate.py` y ejecuta `python3 platform/deploy/local/kube/generate.py`.

## Qué se probó

| | Estado |
|---|---|
| `compose.yaml`: YAML válido, límites en todos los servicios, puertos solo en 127.0.0.1, volúmenes declarados, `service_healthy`, `$$` y `name:` interpretados por `podman-compose 1.6.0` | Revisado |
| Manifiestos de `kube/` contra el esquema de Kubernetes 1.35 (modo estricto) | 17 recursos válidos |
| Objetivos `make up`, `down`, `logs`, `reset` | Comandos verificados en modo simulado |
| `make compose-check` (compose + manifiestos al día + esquema de Kubernetes) | Pasa; rechaza seis tipos de error ensayados a propósito |
| **Ejecución real en Fedora con Podman sin root** | **Pendiente: hazla con la lista de abajo** |

### Lista para registrar en el PR (Fedora, Podman sin root)

```bash
podman info --format 'rootless={{.Host.Security.Rootless}}'     # rootless=true
make up && sleep 90 && make health                              # los 6 servicios en 200
podman ps --format '{{.Names}} {{.Status}}'                     # todo healthy
podman stats --no-stream                                        # memoria de cada contenedor, bajo su límite
make down && make up && make health                             # los datos sobreviven a down
make reset YES=1 && make health                                 # reset funciona
make kube-build && make kube-up && podman pod ps               # plan B (opcional: antes make down)
```
