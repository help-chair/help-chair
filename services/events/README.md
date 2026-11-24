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
uv run pytest                                    # equivalente a `make test`
```

- Sin `DATABASE_URL` se usa SQLite (`db.sqlite3`), no hace falta PostgreSQL en desarrollo.
- El puerto por defecto es `8001` (en el Makefile: `make run PORT=8080`).

