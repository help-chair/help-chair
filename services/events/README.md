# services/events

[English below ↓](#english)

> Gestión de Eventos: recibe, filtra, clasifica, prioriza y enruta eventos (punto de entrada del stack). / Event Management: receives, filters, classifies, prioritises and routes events (stack entry point).

| | |
|---|---|
| **Equipo / Team** | Gestión de Eventos / Event Management |
| **Práctica ITIL v4 / ITIL v4 practice** | Monitoring and Event Management |
| **Imagen / Image** | `ghcr.io/help-chair/hc-events` |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
<!-- Qué hace esta carpeta y qué NO hace -->

### Stack tecnológico
- Lenguaje / framework: Python / Django
- Base de datos: TimescaleDB

### Contrato mínimo de servicio
- [ ] `Dockerfile` y usuario no root
- [ ] `GET /health/live` y `GET /health/ready`
- [ ] Configuración solo por variables de entorno (`.env.example`)
- [ ] Logs en JSON
- [ ] API documentada con OpenAPI en `contracts/`; eventos según `contracts/messages/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-events`
- [ ] `requests`/`limits` de recursos declarados
- [ ] Cierre ordenado con `SIGTERM`
- [ ] Workflow de CI propio, filtrado por esta ruta (ver `../../CONTRIBUTING.md`)

### Ejecución local
```bash
cp .env.example .env
# TODO: comandos para levantar el servicio
```

### Reglas del monorepo
Trabaja **solo dentro de esta carpeta**. Si necesitas tocar otra, abre un PR separado o coordínate con sus dueños. Guía: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

---

## English

### Responsibility
<!-- What this folder does and does NOT do -->

### Tech stack
- Language / framework: _to be defined by the team_
- Database: _to be defined by the team_ (owned by this service)

### Minimum service contract
See the checklist above.

### Running locally
```bash
cp .env.example .env
# TODO: commands to start the service
```

### Monorepo rules
Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../../CONTRIBUTING.en.md).

### Rutas y apps del servicio

| Ruta | App | Descripción |
|---|---|---|
| `GET /health/live` | `core` | Liveness: el proceso responde (`{"status": "ok"}`). |
| `GET /health/ready` | `core` | Readiness: ejecuta `SELECT 1` en la BD. Devuelve `{"status": "ok", "database": "up"}` o `503` con `"database": "down"`. |
| `GET /api/v1/events` | `events` | Lista eventos. |
| `POST /api/v1/events` | `events` | Registra y deduplica eventos. |
| `GET /api/v1/events/{id}` | `events` | Devuelve el detalle de un evento. |
| `/api/schema/`, `/api/docs/` | `config` | Esquema OpenAPI y Swagger UI (drf-spectacular). |
| `/admin/` | `config` | Admin de Django. |

- `core`: salud del servicio (`core/urls.py`, `core/views.py`).
- `events`: lógica de eventos, registrada en `INSTALLED_APPS` (`config/settings.py`) y enrutada en `config/urls.py` con `include("events.urls")`.
- `events/outbox/`: publicación de mensajes al broker con el patrón *outbox* (ver [Publicación al broker](#publicación-al-broker-outbox)).

### Configuración (`SECRET_KEY`)

1. Copia `.env.example` a `.env`.
2. Define `SECRET_KEY` en tu `.env` (genera una con `tests/secretkey_gen.py` o con `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`).
3. Sin `SECRET_KEY` el servicio no arranca (`ImproperlyConfigured`), salvo con `DEBUG=true` o bajo pytest, donde se usa una clave insegura de desarrollo.

No subas tu clave real al repositorio: el `.env` está ignorado por git.

### Ejecución local sin `make` (Windows / PowerShell)

Desde `services/events`:

```powershell
cp .env.example .env
uv sync
uv run python manage.py migrate --noinput
uv run python manage.py runserver 0.0.0.0:8001   # equivalente a `make run`
uv run python manage.py publish_outbox           # publica los mensajes pendientes al broker
uv run pytest                                    # equivalente a `make test`
```

- Sin `DATABASE_URL` se usa SQLite (`db.sqlite3`), no hace falta PostgreSQL en desarrollo.
- El puerto por defecto es `8001` (en el Makefile: `make run PORT=8080`).

### Publicación al broker (outbox)

Los demás servicios se enteran de los cambios de Eventos **sin acoplarse ni perder mensajes** gracias al patrón *outbox*, en dos pasos:

1. **Escritura:** al registrar un evento o cambiar su estado, `events/outbox/messages.py` guarda el mensaje en la tabla `outbox_message` dentro de la **misma transacción**. Si el cambio se revierte, el mensaje también.
2. **Publicación:** `manage.py publish_outbox` lee los mensajes pendientes, los envuelve en el sobre común (`contracts/messages/event-envelope.json`) y los publica en NATS JetStream (`events/outbox/jetstream.py`), con reintentos.

| Mensaje | Subject | Cuándo se escribe |
|---|---|---|
| `event.state_changed` | `events.state_changed` | Alta del evento (`from_state` nulo → `NEW`) y cada transición, incluidas la asignación y el cierre automático de la regla 1 |
| `event.routed` | `events.routed.<destino>` | Listo en `enqueue_routed`; lo usará el enrutamiento de las reglas hacia otros servicios |

- **Stream:** `EVENTS` con los subjects `events.>`; el publicador lo crea si no existe.
- **Idempotencia:** el `id` del sobre es el de `outbox_message` y viaja en la cabecera `Nats-Msg-Id`; JetStream y los consumidores descartan los duplicados.
- **Broker caído:** los mensajes quedan `PENDING` y salen en el siguiente pase, en el mismo orden. Una caída nunca los marca como `FAILED`.
- **Mensaje inválido:** se reintenta con espera exponencial (5 s, 10 s, 20 s… hasta 15 min) y, al llegar a `OUTBOX_MAX_ATTEMPTS`, pasa a `FAILED`. Se revisa y se reintenta desde `/admin/` (*Mensajes de salida*).
- **Registro de errores:** logs JSON (`outbox_broker_unavailable`, `outbox_publish_retry`, `outbox_message_failed`) y el campo `last_error`. Los logs ahora incluyen los campos `extra` (`config/logging.py`).
- **Plan B (REST):** con `OUTBOX_TRANSPORT=http`, el mismo sobre se entrega por `POST` a las URL de `OUTBOX_HTTP_ROUTES`, con la cabecera `Idempotency-Key` y los mismos reintentos (`events/outbox/http.py`).
- **Migraciones:** `0004_outbox_message` crea la tabla y además une las dos `0003` (`priority_modifier` y `recurrence_policy`), que estaban en conflicto.

**Ejecutar el publicador:**

```powershell
uv run python manage.py publish_outbox           # un pase: publica lo pendiente y termina
uv run python manage.py publish_outbox --loop    # worker continuo; termina con SIGTERM
```

| Variable | Por defecto | Para qué |
|---|---|---|
| `BROKER_URL` | vacío | `nats://broker:4222` en compose y Helm; en local, `nats://localhost:4222` |
| `OUTBOX_TRANSPORT` | `jetstream` | `jetstream` o `http` (plan B) |
| `OUTBOX_BATCH_SIZE` | `50` | Mensajes por pase |
| `OUTBOX_MAX_ATTEMPTS` | `10` | Intentos antes de marcar `FAILED` |

- Las demás variables (`OUTBOX_STREAM`, tiempos de espera y rutas del plan B) están en `.env.example`.
- Pruebas: `tests/test_outbox.py`, `tests/test_outbox_relay.py`, `tests/test_outbox_http.py` y `tests/test_outbox_jetstream.py`. Esta última necesita un NATS real (`NATS_TEST_URL=nats://127.0.0.1:4222`); sin él se salta.
- El worker (`publish_outbox --loop`) en el compose y en Helm lo agrega Plataforma (`platform/deploy`).
- Detalle completo (garantías, plan B y qué debe ofrecer cada receptor REST): [`docs/outbox.md`](docs/outbox.md).

