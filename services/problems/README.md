# services/problems

[English below ↓](#english)

> Gestión de Problemas: causa raíz, patrones repetidos y errores conocidos. / Problem Management: root cause, recurring patterns and known errors.

| | |
|---|---|
| **Equipo / Team** | Gestión de Problemas / Problem Management |
| **Práctica ITIL v4 / ITIL v4 practice** | Problem Management + Knowledge Management |
| **Imagen / Image** | `ghcr.io/help-chair/hc-problems` |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
<!-- Qué hace esta carpeta y qué NO hace -->

### Stack tecnológico
- Lenguaje / framework: Python / Django
- Base de datos: PostgreSQL (propia de este servicio)

### Modelo de datos
Los IDs de otros servicios (`asignado_a_id`, `incidente_id`, `articulo_kb_id`) se guardan como texto, **sin llaves foráneas**: cada servicio es dueño de su propia base de datos.

```mermaid
erDiagram
    PROBLEMA ||--o{ PROBLEMA_INCIDENTE : "incidentes"
    PROBLEMA ||--o{ ERROR_CONOCIDO : "errores_conocidos"

    PROBLEMA {
        bigint id PK
        varchar titulo "200"
        text descripcion
        varchar estado "registrado | en_analisis | causa_identificada | error_conocido | resuelto | cerrado"
        varchar prioridad "baja | media | alta | critica"
        varchar origen "manual | patron"
        text causa_raiz "opcional"
        varchar asignado_a_id "ID en Accesos, sin FK"
        timestamptz creado_en
        timestamptz actualizado_en
        timestamptz resuelto_en "nullable"
    }

    PROBLEMA_INCIDENTE {
        bigint id PK
        bigint problema_id FK
        varchar incidente_id "ID en Incidencias, sin FK"
        timestamptz vinculado_en
    }

    ERROR_CONOCIDO {
        bigint id PK
        bigint problema_id FK
        varchar titulo "200"
        text descripcion
        text causa_raiz
        text workaround
        varchar articulo_kb_id "ID en Knowledge, sin FK"
        boolean activo "default true"
        timestamptz creado_en
        timestamptz actualizado_en
    }
```

`PROBLEMA_INCIDENTE` tiene una restricción única `(problema_id, incidente_id)`: un incidente no puede vincularse dos veces al mismo problema.

### Contrato mínimo de servicio
- [ ] `Dockerfile` y usuario no root
- [ ] `GET /health/live` y `GET /health/ready`
- [ ] Configuración solo por variables de entorno (`.env.example`)
- [ ] Logs en JSON
- [ ] API documentada con OpenAPI en `contracts/`; eventos según `contracts/messages/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-problems`
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
