# services/knowledge

[English below ↓](#english)

> Base de Conocimiento: artículos y soluciones, consumida por API. / Knowledge Base: articles and solutions, consumed via API.

| | |
|---|---|
| **Equipo / Team** | Gestión de Problemas / Problem Management |
| **Práctica ITIL v4 / ITIL v4 practice** | Problem Management + Knowledge Management |
| **Imagen / Image** | `ghcr.io/help-chair/hc-knowledge` |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
<!-- Qué hace esta carpeta y qué NO hace -->

El dominio inicial de artículos y categorías, su admin y migración se documentan en
[Esquema de artículos (#109 / #132)](docs/article-schema.md).
La API de negocio y su contrato siguen pendientes; este incremento no implementa CRUD ni búsqueda.

### Stack tecnológico
- Lenguaje / framework: Python / Django
- Base de datos: PostgreSQL 16, propia de este servicio.

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
cp .env.example .env
# TODO: comandos para levantar el servicio
```

### Reglas del monorepo
Trabaja **solo dentro de esta carpeta**. Si necesitas tocar otra, abre un PR separado o coordínate con sus dueños. Guía: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

---

## English

### Responsibility
<!-- What this folder does and does NOT do -->

The initial article/category models, admin and migration are documented in
[Article schema (#109 / #132)](docs/article-schema.md).
The business API and contract remain pending; this increment does not implement CRUD or search.

### Tech stack
- Language / framework: _to be defined by the team_
- Database: PostgreSQL 16 (owned by this service).

### Minimum service contract
See the checklist above.

### Running locally
```bash
cp .env.example .env
# TODO: commands to start the service
```

### Monorepo rules
Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../../CONTRIBUTING.en.md).
