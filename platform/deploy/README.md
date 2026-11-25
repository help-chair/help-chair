# platform/deploy

[English below ↓](#english)

> Aprovisionamiento por stack: Kubernetes, Helm, docker-compose. / Per-stack provisioning: Kubernetes, Helm, docker-compose.

| | |
|---|---|
| **Equipo / Team** | Plataforma / Platform |
| **Práctica ITIL v4 / ITIL v4 practice** | Platform and Deployment |
| **Imagen / Image** | `ghcr.io/help-chair/hc-platform-deploy` |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
<!-- Qué hace esta carpeta y qué NO hace -->

### Stack tecnológico
- Lenguaje / framework: Django
- Base de datos: _por definir por el equipo_ (propia de este servicio)

### Contrato mínimo de servicio
- [ ] `Dockerfile` y usuario no root
- [ ] `GET /health/live` y `GET /health/ready`
- [ ] Configuración solo por variables de entorno (`.env.example`)
- [ ] Logs en JSON
- [ ] API documentada con OpenAPI en `contracts/`; eventos según `contracts/messages/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-platform-deploy`
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
