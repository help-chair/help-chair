# services/incidents

[English below ↓](#english)

> Gestión de Incidencias: fallas y degradaciones de servicio. / Incident Management: service failures and degradations.

| | |
|---|---|
| **Equipo / Team** | Equipo 4: Gestión de Incidencias / Incident Management (@decko67, @DiegoMH890) |
| **Práctica ITIL v4 / ITIL v4 practice** | Incident Management |
| **Imagen / Image** | `ghcr.io/help-chair/hc-incidents` |
| **Contrato / Contract** | [`contracts/incidents/openapi.yaml`](../../contracts/incidents/openapi.yaml) (v0, borrador) |
| **Puerto / Port** | 8004 (BD del compose: 5444) |

## Español

### Responsabilidad

**Hace:** registra los incidentes (algo dejó de funcionar o funciona mal), calcula su prioridad con la matriz impacto × urgencia, los asigna a un agente y lleva su ciclo de vida hasta el cierre. El objetivo ITIL es **restablecer el servicio lo antes posible**.

**No hace:**
- Investigar la causa raíz → **Problemas** (consume nuestros incidentes por ID).
- Atender solicitudes donde nada está roto (p. ej. «necesito una laptop») → **Peticiones**.
- Guardar usuarios, servicios ni el SLA → **Accesos** y **Eventos**. Aquí solo se guardan sus **IDs como texto**, nunca una llave foránea entre bases de datos.
- Clasificar eventos → **Eventos** decide qué se convierte en incidente (regla 6).

### Stack tecnológico

- Python 3.12, Django 5 + Django REST Framework, drf-spectacular (OpenAPI).
- PostgreSQL 16 propia del servicio (`incidents-db`). Sin `DATABASE_URL` se usa SQLite, útil para pruebas.

### Modelo

`Incident` ([`incidents/models.py`](incidents/models.py)):

| Campo | Qué es |
|---|---|
| `id`, `code` | ID numérico y código legible (`INC-000042`) |
| `title`, `description` | Qué está fallando |
| `impact`, `urgency` | `alto`/`medio`/`bajo` y `alta`/`media`/`baja` |
| `priority` | `P1`–`P4`. **Se calcula sola**: no se puede asignar a mano |
| `status` | Estado ITIL (ver abajo). Siempre nace en `nuevo` |
| `reported_by`, `assigned_to`, `assignment_group` | IDs de **Accesos** |
| `affected_service`, `source_event_id` | IDs de **Eventos** |
| `problem_id` | ID de **Problemas** |
| `sla_due_at` | Fecha objetivo de resolución (se calculará en la Fase 2) |
| `created_at`, `updated_at`, `resolved_at`, `closed_at` | Fechas; las de resolución y cierre se llenan solas |

### Matriz de prioridad (impacto × urgencia)

| Impacto \ Urgencia | Alta | Media | Baja |
|---|---|---|---|
| **Alto** | P1 Crítica | P2 Alta | P3 Media |
| **Medio** | P2 Alta | P3 Media | P4 Baja |
| **Bajo** | P3 Media | P4 Baja | P4 Baja |

Implementada en [`incidents/priority.py`](incidents/priority.py) (`calculate_priority`). Se recalcula cada vez que se guarda el incidente.

### Estados y transiciones permitidas

```
nuevo ──► asignado ──► en_proceso ⇄ en_espera
  │          │             │
  │          │             └──► resuelto ──► cerrado (final)
  │          │                     │
  │          │                     └──► reabierto ──► asignado / en_proceso
  └──────────┴──► rechazado (final) · cancelado (final; también desde en_proceso y en_espera)
```

- Para pasar a `asignado` hace falta `assigned_to`.
- `rechazado`: no era un incidente (p. ej. era una petición). `cancelado`: ya no hace falta atenderlo.
- Tabla exacta: `TRANSITIONS` en [`incidents/models.py`](incidents/models.py). Una transición no permitida responde **400**.

### API (v0)

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/api/incidents/v1/incidents/` | Lista paginada (50 por página), P1 primero. Filtros: `?status=`, `?priority=`, `?assigned_to=` |
| `POST` | `/api/incidents/v1/incidents/` | Registra un incidente (`title`, `impact`, `urgency`, `reported_by` obligatorios) |
| `GET` | `/api/incidents/v1/incidents/{id}/` | Detalle |
| `PATCH` | `/api/incidents/v1/incidents/{id}/` | Asignar, cambiar impacto o urgencia, o cambiar de estado |


No hay `PUT` ni `DELETE`: un incidente no se borra, se cancela. Documentación interactiva en `http://localhost:8004/api/docs/`.

```bash
curl -X POST localhost:8004/api/incidents/v1/incidents/ -H "Content-Type: application/json" \
  -d '{"title":"No abre nómina","impact":"medio","urgency":"alta","reported_by":"usr-ana"}'
```

### Ejecución local

**Opción A, en contenedor con PostgreSQL** (la forma recomendada; solo necesitas Docker o Podman). Desde la raíz del repo:

```bash
docker compose -f platform/deploy/local/compose.yaml up -d --build incidents incidents-db
curl localhost:8004/health/ready          # {"status": "ok", "database": "up"}
docker compose -f platform/deploy/local/compose.yaml exec incidents python manage.py loaddata incidentes_ejemplo
docker compose -f platform/deploy/local/compose.yaml exec incidents python manage.py createsuperuser
```

Admin en `http://localhost:8004/admin/`. Con Podman, cambia `docker compose` por `podman compose`.

**Opción B, con `make`** (Linux, macOS o Git Bash con make y uv):

```bash
cd services/incidents
make setup   # dependencias + .env
make run     # migra y arranca en :8004 con SQLite
make seed    # 4 incidentes de ejemplo
make test    # pruebas con cobertura
make lint    # ruff
make openapi # regenera contracts/incidents/openapi.yaml
```

**Opción C, Windows sin `make`** (PowerShell, requiere Python **3.12**):

```powershell
cd services\incidents
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
copy .env.example .env      # y pon DEBUG=true
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py loaddata incidentes_ejemplo
.venv\Scripts\python manage.py runserver 8004
.venv\Scripts\python -m pytest
```

**Opción D, solo pruebas en contenedor** (sin instalar Python):

```bash
docker run --rm -e DEBUG=true -v "$PWD:/app" -w /app python:3.12-slim \
  sh -c "pip install -q -r requirements-dev.txt && pytest && ruff check . && ruff format --check ."
```

### Contrato mínimo de servicio

- [x] `Dockerfile` y usuario no root
- [x] `GET /health/live` y `GET /health/ready`
- [x] Configuración solo por variables de entorno (`.env.example`)
- [x] Logs en JSON
- [x] API documentada con OpenAPI en `contracts/incidents/` (v0)
- [ ] Eventos según `contracts/messages/` (el sobre común aún no existe; Fase 2)
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-incidents` (Jenkins, Fase 2)
- [ ] `requests`/`limits` de recursos declarados (Helm, Fase 2–3)
- [x] Cierre ordenado con `SIGTERM` (gunicorn como PID 1)
- [ ] `Jenkinsfile` propio, filtrado por esta ruta (Fase 2)

### Pendiente para la Fase 2

- **Autenticación:** validar el JWT de Accesos. Hoy la API v0 **no tiene autenticación**: no exponerla fuera del entorno local.
- **SLA:** calcular `sla_due_at` con el SLA por prioridad de Eventos (D-11) y pausarlo en `en_espera`.
- **Historial:** bitácora de cambios (quién, qué y cuándo) para el detalle del incidente.
- **Mensajería:** consumidor de eventos (`manage.py consume_events`) y publicación de `incident.*` para Problemas, según `contracts/messages/`.
- **Categorías** de incidentes (#27).

---

## English

### Responsibility

**Does:** records incidents (something stopped working or works poorly), computes their priority with the impact × urgency matrix, assigns them to an agent and tracks their lifecycle until closure.
**Does not:** root-cause analysis (Problems), standard requests (Requests), or store users, services or SLAs (Access and Events). Other services' data is stored **only as text IDs**.

### Quick start

```bash
docker compose -f platform/deploy/local/compose.yaml up -d --build incidents incidents-db
curl localhost:8004/health/ready
```

API: `GET/POST /api/incidents/v1/incidents/`, `GET/PATCH /api/incidents/v1/incidents/{id}/`. Contract: [`contracts/incidents/openapi.yaml`](../../contracts/incidents/openapi.yaml). The Spanish section above has the model, priority matrix, states and every way of running the service.


### Monorepo rules

Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../../CONTRIBUTING.en.md).
