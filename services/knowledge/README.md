# services/knowledge

[English below ↓](#english)

> Base de Conocimiento: artículos y soluciones, consumida por API. / Knowledge Base: articles and solutions, consumed via API.

| | |
|---|---|
| **Equipo / Team** | Gestión de Problemas / Problem Management |
| **Práctica ITIL v4 / ITIL v4 practice** | Problem Management + Knowledge Management |
| **Imagen / Image** | `ghcr.io/help-chair/hc-knowledge` |
| **Contratos / Contracts** | `contracts/knowledge/` |
| **Puerto / Port** | `8006` (BD local en `5446`) |

## Español

### Responsabilidad

**Qué hace esta carpeta:**

- Guarda los artículos de la Base de Conocimiento: soluciones, guías y pasos para resolver fallas comunes.
- Permite buscarlos por texto (búsqueda de texto completo de PostgreSQL) y los entrega por API.
- Es consultada por Eventos, Incidencias, Problemas y el frontend del Service Desk, que piden artículos cuando los necesitan.

**Qué NO hace:**

- No registra problemas ni errores conocidos: eso es de `services/problems`. Un error conocido puede apuntar a un artículo, pero aquí no se guarda el error.
- No decide cuándo usar un artículo: solo responde consultas. Quien la llama decide qué hacer con la respuesta.
- No autentica usuarios: eso es de Accesos.
- No lee la base de datos de ningún otro servicio ni expone la suya: se consume solo por API (decisión D-05 en [`docs/DECISIONS.md`](../../docs/DECISIONS.md)).

El dominio inicial de artículos y categorías, su admin y migración se documentan en
[Esquema de artículos (#109 / #132)](docs/article-schema.md).
La API de negocio y su contrato siguen pendientes; este incremento no implementa CRUD ni búsqueda.

### Stack tecnológico
- Lenguaje / framework: Python 3.12 / Django 5 + Django REST Framework
- OpenAPI: `drf-spectacular`
- Base de datos: PostgreSQL 16 propia de este servicio (SQLite en local si no se define `DATABASE_URL`)

### Contrato mínimo de servicio
- [ ] `Dockerfile` y usuario no root
- [ ] `GET /health/live` y `GET /health/ready`
- [ ] Configuración solo por variables de entorno (`.env.example`)
- [ ] Logs en JSON
- [ ] API documentada con OpenAPI en `contracts/`; eventos según `contracts/messages/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-knowledge`
- [ ] `requests`/`limits` de recursos declarados
- [ ] Cierre ordenado con `SIGTERM`
- [ ] Workflow de CI propio, filtrado por esta ruta (ver `../../CONTRIBUTING.md`)

### Ejecución local

```bash
cd services/knowledge
make setup                   # crea .env y el entorno virtual
source .venv/bin/activate    # solo si no tienes uv (ver nota)
make test                    # pruebas con cobertura
make lint                    # ruff, sin modificar archivos
make run                     # migra y arranca en http://localhost:8006
```

> **Nota:** si tienes [uv](https://docs.astral.sh/uv/) instalado, `make` lo usa solo y no hace falta activar nada. Sin uv, el `make` que trae macOS (3.81) no encuentra los programas del entorno virtual, por eso hay que activarlo antes con `source .venv/bin/activate`.

Con eso corre sobre SQLite, suficiente para desarrollar y para `make test`. Para trabajar contra la PostgreSQL del servicio, levántala con el compose y descomenta `DATABASE_URL` en tu `.env`:

```bash
podman compose -f ../../platform/deploy/local/compose.yaml up -d knowledge-db
make migrate && make run
```

Para levantar el stack completo (cada servicio con su base) desde la raíz del repo:

```bash
make up        # podman compose (o docker compose) con platform/deploy/local/compose.yaml
```

Comprobación rápida:

```bash
curl http://localhost:8006/health/ready
# {"status": "ok", "database": "up"}
```

### API

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/health/live` | El proceso responde. |
| `GET` | `/health/ready` | El proceso responde y la base es alcanzable. |
| `GET` | `/api/schema/` | Contrato OpenAPI generado por `drf-spectacular`. |
| `GET` | `/api/docs/` | Documentación navegable (Swagger). |

Las rutas de artículos y búsqueda se documentan en `contracts/knowledge/`. Para exportar el contrato después de cambiar la API:

```bash
make openapi
```

### Variables de entorno

Las define `.env.example`:

| Variable | Para qué | Por omisión |
|---|---|---|
| `SERVICE_NAME` | Nombre del servicio en los logs. | `knowledge` |
| `DEBUG` | Modo desarrollo. Sin `DEBUG=true` hay que definir `SECRET_KEY`. | `false` |
| `SECRET_KEY` | Clave de Django. Obligatoria fuera de desarrollo. | — |
| `ALLOWED_HOSTS` | Hosts permitidos. | `*` |
| `LOG_LEVEL` | Nivel de los logs (JSON). | `INFO` |
| `PORT` | Puerto del servidor en el contenedor. | `8006` |
| `DATABASE_URL` | Base PostgreSQL del servicio. Sin ella se usa SQLite. | — |
| `BROKER_URL` | Broker de mensajes (fase 2). | — |

### Reglas del monorepo
Trabaja **solo dentro de esta carpeta**. Si necesitas tocar otra, abre un PR separado o coordínate con sus dueños. Guía: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

---

## English

### Responsibility

**What this folder does:** stores the Knowledge Base articles (solutions, guides and steps to fix common failures); lets clients search them by text (PostgreSQL full-text search) and serves them via API; it is queried by Events, Incidents, Problems and the Service Desk frontend.

**What it does NOT do:** it does not record problems or known errors (`services/problems` does; a known error may point to an article, but the error is not stored here); it does not decide when an article is used, it only answers queries; it does not authenticate users (Access does); it never reads another service's database nor exposes its own — it is consumed only via API (decision D-05 in [`docs/DECISIONS.md`](../../docs/DECISIONS.md)).

The initial article/category models, admin and migration are documented in
[Article schema (#109 / #132)](docs/article-schema.md).
The business API and contract remain pending; this increment does not implement CRUD or search.

### Tech stack
- Language / framework: Python 3.12 / Django 5 + Django REST Framework, OpenAPI via `drf-spectacular`
- Database: PostgreSQL 16 owned by this service (SQLite locally when `DATABASE_URL` is unset)

### Minimum service contract
See the checklist above.

### Running locally
```bash
cd services/knowledge
make setup                   # creates .env and the virtualenv
source .venv/bin/activate    # only if you don't have uv
make test && make lint
make run                     # http://localhost:8006
```

Without uv, macOS's bundled `make` (3.81) can't find the virtualenv's programs, so activate it first. To use the service's PostgreSQL, run `podman compose -f ../../platform/deploy/local/compose.yaml up -d knowledge-db` and uncomment `DATABASE_URL` in your `.env`. `make up` from the repo root starts the whole stack. See the Spanish section above for the endpoint and environment variable tables.

### Monorepo rules
Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../../CONTRIBUTING.en.md).
