# services/requests

[English below ↓](#english)

> Gestión de Peticiones: solicitudes estándar del catálogo. / Request Management: standard catalogue requests.

| | |
|---|---|
| **Equipo / Team** | Gestión de Peticiones / Request Management |
| **Práctica ITIL v4 / ITIL v4 practice** | Service Request Management |
| **Imagen / Image** | `ghcr.io/help-chair/hc-requests` |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
<!-- Qué hace esta carpeta y qué NO hace -->

### Stack tecnológico
- Lenguaje / framework: Python / Django
- Base de datos: _por definir por el equipo_ (propia de este servicio)

### Contrato mínimo de servicio
- [ ] `Dockerfile` y usuario no root
- [ ] `GET /health/live` y `GET /health/ready`
- [ ] Configuración solo por variables de entorno (`.env.example`)
- [ ] Logs en JSON
- [ ] API documentada con OpenAPI en `contracts/`; eventos según `contracts/messages/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-requests`
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


## Servicio de Peticiones

Gestiona las peticiones de servicio de la mesa de ayuda: catálogo de servicios
solicitables y ciclo de vida de cada petición.

### Modelos

- `ServicioSolicitable`: catálogo de servicios que se pueden pedir.
- `Peticion`: estados `nuevo → asignado → en_proceso → resuelto → cerrado`,
  más `reabierto` y `cancelado`. Las transiciones válidas están en
  `Peticion.TRANSICIONES`.
- Los IDs de usuario y de evento (`solicitante_id`, `asignado_a_id`,
  `evento_id`) son enteros, no llaves foráneas, porque viven en otros servicios.

### Endpoints

- `GET/POST /api/peticiones/`, `GET/PUT/PATCH/DELETE /api/peticiones/{id}/`
- `GET /api/servicios/`
- `GET /api/schema/` y `GET /api/docs/` (OpenAPI y Swagger)
- `GET /health/live` y `GET /health/ready`

El contrato publicado está en `contracts/requests/openapi.yaml`.

### Correrlo en local

1. Levantar la base: `podman-compose -f ../../platform/deploy/local/compose.yaml up -d requests-db`
2. Copiar `.env.example` a `.env` y definir `SECRET_KEY` y
   `DATABASE_URL=postgres://requests:requests@localhost:5443/requests`
3. `pip install -r requirements.txt -r requirements-dev.txt`
4. `python manage.py migrate`
5. `python manage.py runserver 8003`

Pruebas y estilo: `pytest` y `ruff check .`