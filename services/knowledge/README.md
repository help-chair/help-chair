# Knowledge

[English below](#english)

## Español

### Alcance y requisitos

Servicio independiente del equipo 5 para artículos y categorías de conocimiento,
con PostgreSQL 16 propio. Python 3.12, Django/DRF, uv, Make y Podman en Linux/WSL.
El [esquema y sus límites](docs/article-schema.md) incluyen migración y admin.
La [matriz de evidencia y conciliación](docs/foundations-evidence.md) distingue
pruebas locales, cobertura KB de #111/#135/#136 y revisiones pendientes.
El [contrato v0 propuesto de #230](https://github.com/help-chair/help-chair/blob/8666c03416c7862e470efaf5c7a273ec32c30087/contracts/knowledge/openapi.yaml)
está en otra rama; sus operaciones de negocio no están implementadas.
Las referencias de Accesos son externas; no se consultan otras bases de datos.
El CRUD REST, búsqueda y permisos de negocio corresponden a incrementos posteriores.
Contrato: `contracts/knowledge/`; la exportación de las rutas actuales no sustituye
el diseño v0 revisado en #112/#134. `make openapi` exige OPENAPI_OUTPUT con una ruta
explícita fuera de `contracts/`; rechaza el destino canónico. El resultado describe
solo el runtime y se mantiene separado del contrato de negocio previsto.

### Configuración del proceso

El sistema, contenedor o CI suministra el entorno antes de iniciar el proceso.
El servicio no crea, copia ni carga `.env`. `.env.example` es solo un inventario
con asignaciones vacías; no se usa para ejecutar. Secretos obligatorios ausentes
impiden el arranque indicando únicamente el nombre de la variable. No hay clave
predeterminada ni fallback a SQLite, tampoco al ejecutar pytest.

| Variable | Obligatoria | Finalidad y formato |
|---|---|---|
| SECRET_KEY | Sí | Clave Django privada, no vacía, gestionada fuera del repositorio |
| DATABASE_URL | Sí | URI PostgreSQL con usuario, contraseña, host y nombre de BD |
| ALLOWED_HOSTS | Sí | Hosts permitidos separados por comas, sin protocolo ni puerto |
| DEBUG | No | Booleano; el comportamiento normal es sin depuración |
| SERVICE_NAME | No | Nombre del servicio usado en logs |
| LOG_LEVEL | No | Nivel de logging admitido por Python |
| PORT | No | Puerto TCP del servidor gunicorn; entero positivo válido |
| WEB_CONCURRENCY | No | Cantidad positiva de workers gunicorn |
| GRACEFUL_TIMEOUT | No | Segundos positivos para finalizar peticiones al parar |
| DATABASE_CONNECT_TIMEOUT | No | Segundos positivos de espera al conectar PostgreSQL |

Compose necesita también POSTGRES_USER, POSTGRES_PASSWORD y POSTGRES_DB del entorno
privado para provisionar la BD; deben corresponder con DATABASE_URL. Son nombres de
usuario/BD y una contraseña privada no vacía. KNOWLEDGE_IMAGE selecciona la imagen
local; KNOWLEDGE_API_PORT y KNOWLEDGE_DB_PORT permiten puertos de ensayo aislados.
KNOWLEDGE_STOP_GRACE_PERIOD es una duración Compose; si se aumenta GRACEFUL_TIMEOUT,
ajustarla para que el presupuesto del motor siga siendo mayor.

No publicar valores en comandos, historial, logs, capturas, PR o imágenes.
Usar el entorno privado del sistema/CI o un gestor de secretos; nunca ARG de build.
`.gitignore` y `.dockerignore` excluyen variantes `.env`, claves privadas y `secrets/`.
Antes de publicar, revisar archivos, commits y artefactos con salida saneada.

### Puertos y ejecución local

API: 8006. PostgreSQL: host 5446 → contenedor 5432. Django en el host/WSL conecta
por `localhost:5446`; dentro de la red Compose conecta por `knowledge-db:5432`.
Son conexiones diferentes. PostgreSQL debe estar provisionado con su volumen y
credenciales privadas antes de migrar; no reutilizar una BD de otro servicio.

Desde `services/knowledge`, con el entorno ya suministrado:

```bash
make setup
make migrate
uv run --frozen python manage.py showmigrations articles
make migrate
make run
```

`setup` usa el lock existente; no configura secretos. La segunda migración no debe
tener operaciones pendientes. `run` también migra antes de servir en desarrollo.
Para cambiar su puerto usar la variable Make `PORT`; el archivo `.env` no configura
Make. El admin requiere un usuario staff de ensayo creado interactivamente; su PK
no es la identidad externa del autor.

### Seed y calidad

Solo en una BD propia de ensayo:

```bash
make seed CONFIRM_DEMO=1
make seed CONFIRM_DEMO=1
make lint
make test
make build CONTAINER=podman
```

El seed usa exclusivamente `articles/fixtures/kb_demo.json`: dos categorías y cuatro
artículos sintéticos de UUID fijos. Recargar sobrescribe esos ejemplos, conserva
sus IDs y no elimina otras filas. Sin confirmación no escribe. No se ejecuta al
arrancar, migrar o construir. Las pruebas requieren un PostgreSQL aislado y un
usuario de ensayo con permiso para crear su BD de test; las credenciales se
generan/inyectan privadamente. No ejecutar `make lock` para estas comprobaciones.

### Imagen y arranque operativo

La imagen local es `ghcr.io/help-chair/hc-knowledge:dev`. El build reúne estáticos
con settings exclusivos sin clave ni BD. La imagen conserva UID/GID 10001 y arranca
gunicorn directamente como proceso principal. El operador inyecta las variables
en ejecución; las siguientes opciones reenvían el entorno sin escribir valores:

```bash
podman run --rm --env SECRET_KEY --env DATABASE_URL --env ALLOWED_HOSTS \
  ghcr.io/help-chair/hc-knowledge:dev python manage.py migrate --noinput
podman run -d --name hc-knowledge --env SECRET_KEY --env DATABASE_URL \
  --env ALLOWED_HOSTS -p 8006:8006 ghcr.io/help-chair/hc-knowledge:dev
podman stop --time 40 hc-knowledge
podman start hc-knowledge
```

La BD debe ser alcanzable desde la red de esos contenedores; el operador añade
la red provisionada si corresponde. No pasar la URI del host suponiendo que
`localhost` dentro del contenedor representa al host. Variables opcionales se
reenvían igualmente por nombre cuando se necesiten.

`compose.yaml` de esta carpeta ejecuta exclusivamente Knowledge y su PostgreSQL.
`knowledge-migrate` es una tarea previa única; el servidor usa después su CMD
directo, con 40 segundos para parar. El volumen `knowledge-data` pertenece al
proyecto Compose. Desde esta carpeta, con variables reales ya suministradas:

```bash
podman compose --env-file /dev/null -f compose.yaml up --build -d
podman compose --env-file /dev/null -f compose.yaml stop knowledge
podman compose --env-file /dev/null -f compose.yaml start knowledge
```

`--env-file /dev/null` evita la carga implícita de `.env` por Compose. Usar un
proveedor que comunique los secretos por la API privada del motor, no mediante
argumentos `-e NOMBRE=valor` ni salida verbose/config expandida. El ensayo usa
Docker Compose sobre el socket privado de Podman; no necesita Docker Desktop.
El Compose global `platform/deploy/local/compose.yaml` aún requiere que Plataforma
sustituya sus valores incrustados por referencias de entorno. Ese cambio global
no está incluido en este incremento del servicio.

### Comprobaciones y recuperación

```bash
curl --fail http://localhost:8006/health/live
curl --fail http://localhost:8006/health/ready
```

Live no depende de BD; ready hace SELECT 1. Con API ya arrancada, detener solo su
BD de ensayo debe mantener live en 200 y producir ready 503 con `database: down`;
al restaurarla ready vuelve a 200. Un arranque frío bloqueado por migrate o
depends_on es un caso diferente. Ready no demuestra que existan las tablas:
comprobar también la migración y lectura de artículos.

Los logs del servidor y aplicación son JSON a stderr, sin texto de excepciones;
access registra método, estado y duración, no query, URL o cabeceras. Las tareas
Make/migrate/seed tienen salida de consola de operación. No volcar entornos o
DSN completos para diagnosticar errores. SIGTERM permite terminar peticiones;
reservar al motor un tiempo superior al graceful-timeout. Tras reiniciar API/BD
conservar el volumen y verificar IDs/recuentos; no usar `down -v` o flush.

La integración del esquema depende del PR #228. Build/ejecución local no acreditan
publicación de imagen, despliegue, pipeline o revisión de consumidores.
Seguir [CONTRIBUTING](../../CONTRIBUTING.md) y CODEOWNERS para la entrega.

## English

### Scope and requirements

Team 5 owns this independent knowledge article/category service and its PostgreSQL
16 database. Use Python 3.12, Django/DRF, uv, Make and Podman on Linux/WSL.
The [schema and limitations](docs/article-schema.md) cover migration and admin.
The [evidence and reconciliation](docs/foundations-evidence.md) separates local
verification, the Knowledge portion of #111/#135/#136 and pending reviews.
The [proposed contract in #230](https://github.com/help-chair/help-chair/blob/8666c03416c7862e470efaf5c7a273ec32c30087/contracts/knowledge/openapi.yaml)
lives on a separate branch; its business operations are not implemented.
Access identities remain external references; no other service database is read.
REST CRUD, search and business authorization belong to subsequent increments.
The reviewed v0 contract belongs in `contracts/knowledge/` through #112/#134;
exporting the currently implemented routes does not replace it. `make openapi`
requires an explicit OPENAPI_OUTPUT path outside `contracts/` and rejects contract
overwrites. Its result describes only the runtime, separately from business design.

### Process configuration

The system/container/CI supplies the environment before startup. The service does
not create, copy or load `.env`. `.env.example` is an empty documentary inventory.
Missing required configuration prevents startup with the variable name only.
There is no default secret or implicit SQLite backend, including under pytest.

| Variable | Required | Purpose and format |
|---|---|---|
| SECRET_KEY | Yes | Nonempty private Django key managed outside the repository |
| DATABASE_URL | Yes | PostgreSQL URI containing user, password, host and database |
| ALLOWED_HOSTS | Yes | Comma-separated allowed hostnames, without scheme or port |
| DEBUG | No | Boolean; normal operation disables debugging |
| SERVICE_NAME | No | Service name included in logs |
| LOG_LEVEL | No | Supported Python logging level |
| PORT | No | Valid positive TCP port for gunicorn |
| WEB_CONCURRENCY | No | Positive number of gunicorn workers |
| GRACEFUL_TIMEOUT | No | Positive request shutdown budget in seconds |
| DATABASE_CONNECT_TIMEOUT | No | Positive PostgreSQL connection timeout in seconds |

Compose also requires privately supplied POSTGRES_USER, POSTGRES_PASSWORD and
POSTGRES_DB matching DATABASE_URL: user/database names and a nonempty private
password. KNOWLEDGE_IMAGE selects the local image; KNOWLEDGE_API_PORT and
KNOWLEDGE_DB_PORT allow isolated test ports.
KNOWLEDGE_STOP_GRACE_PERIOD is a Compose duration; increase it when raising
GRACEFUL_TIMEOUT so the engine always allows a longer shutdown budget.

Keep values out of command history, logs, screenshots, PRs and images. Supply
them privately through the system/CI environment or a secrets manager, never
build ARGs. Ignore rules exclude private `.env` variants, keys and `secrets/`.
Review files, commits and artifacts with sanitized output before publication.

### Local execution, seed and quality

API: 8006. PostgreSQL host port 5446 maps to internal 5432. Host/WSL uses
`localhost:5446`; containers on the Compose network use `knowledge-db:5432`.
Provision the service's own database, volume and private credentials first.
With the process environment already supplied, from `services/knowledge` run:

```bash
make setup
make migrate
uv run --frozen python manage.py showmigrations articles
make migrate
make run
```

Setup uses the existing lock without configuring secrets. The second migration
must have no pending operations. Development `run` also migrates before serving;
change its port with the Make variable PORT, not an `.env` entry. Create any local
test staff user interactively; its PK is not the external article author identity.

Only against an isolated test database:

```bash
make seed CONFIRM_DEMO=1
make seed CONFIRM_DEMO=1
make lint
make test
make build CONTAINER=podman
```

The sole seed source is `articles/fixtures/kb_demo.json`: two synthetic categories
and four articles with stable UUIDs. Reloading overwrites those examples, preserves
their IDs and leaves other rows intact. Without confirmation it performs no writes.
Seed never runs automatically during startup, migration or build. Tests need their
own PostgreSQL and a privately provisioned role allowed to create the test DB.
Do not regenerate the lock for these checks.

### Image, Compose and verification

Image: `ghcr.io/help-chair/hc-knowledge:dev`. Static assets are built with separate
settings requiring no key or database. UID/GID 10001 runs gunicorn directly as the
main process. The Podman commands in the Spanish section forward variables by
name, migrate once, run, stop with an explicit budget and restart. Optional
variables are also forwarded by name. Supply a reachable database and the
provisioned container network as needed: container localhost is not the host.

This directory's `compose.yaml` runs only Knowledge and its PostgreSQL. The
`knowledge-migrate` one-shot task precedes the server, which uses the direct CMD
and a 40-second stop budget. The Compose project owns `knowledge-data`. Run the
Compose up/stop/start commands in the Spanish section from this directory.
`--env-file /dev/null` disables implicit `.env` loading. Use a provider communicating
secrets through the private engine API, excluding expanded secrets from command
arguments or verbose/config output. The verification uses Docker Compose with a
private Podman socket, without Docker Desktop. The shared global Compose still
needs Platform to replace embedded values with environment references; that
global change is outside this service increment.

Check `/health/live` and `/health/ready` on API port 8006. After startup, stopping
only the test database must preserve live 200 and return ready 503 with
`database: down`; restoring it must recover ready 200. A cold start waiting for
migration/depends_on is a separate case. SELECT 1 does not prove schema readiness:
also verify the migration and article query.

Server/application logs are JSON on stderr without exception text; access logs
contain method, status and duration, excluding URL/query/headers. Make/migration/
seed output is operational console output. Never dump environments or DSNs for
diagnosis. SIGTERM permits in-flight work to finish; allow more time in the engine
than graceful-timeout. Verify IDs/counts after restart while retaining the volume;
do not use `down -v` or flush.

The schema depends on PR #228. Local build/run does not prove image publication,
deployment, pipeline execution or consumer approval. Follow
[CONTRIBUTING (Spanish, primary)](../../CONTRIBUTING.md) and CODEOWNERS for delivery.
