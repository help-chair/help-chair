# platform/deploy

[English below ↓](#english)

> Infraestructura de despliegue de Help Chair: entorno local, clúster de testing y chart de Helm por empresa. / Help Chair deployment infrastructure: local environment, testing cluster and per-company Helm chart.

| | |
|---|---|
| **Equipo / Team** | Plataforma / Platform (Equipo 7) |
| **Práctica ITIL v4 / ITIL v4 practice** | Deployment Management / Infrastructure and Platform Management |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
**Hace:**
- **Entorno local** (`local/`): el compose que levanta el stack completo en la máquina de cada integrante, y el plan B con `podman kube play`.
- **Clúster de testing** (`cluster/`): scripts y runbook de k3s en una VM de Google Cloud, con ingress, metrics-server, accesos de solo lectura por equipo y apagado y encendido para controlar costos.
- **Chart de Helm** (`helm/stack/`): la plantilla reutilizable del stack de una empresa (un servicio con su PostgreSQL por archivo de `services/`, broker, Mailpit, ingress, aislamiento y cuotas).

**No hace:** no contiene el código de los servicios, ni del gateway (`platform/gateway/`), ni del frontend. Cada equipo aporta solo `helm/stack/services/<su-servicio>.yaml`.

### Mapa

| Carpeta | Para qué | Empieza por |
|---|---|---|
| [`local/`](local/README.md) | `make up`, `down`, `logs`, `reset`; límites de recursos; plan B | `make up` |
| [`cluster/`](cluster/README.md) | Crear y operar el clúster de testing | `scripts/00-gcp-create-vm.sh` |
| [`helm/stack/`](helm/stack/README.md) | Desplegar el stack de una empresa; cómo agregar un servicio | `make helm-check` |

### Comandos desde la raíz del repositorio

| Comando | Qué hace |
|---|---|
| `make up` · `down` · `logs` · `reset` · `health` | Entorno local |
| `make kube-build` · `kube-up` · `kube-down` · `kube-reset` | Plan B del entorno local |
| `make helm-check` | `helm lint` + `helm template` de dev, testing y production (y kubeconform) |
| `make testing-down` · `testing-up` | Apaga y enciende la VM de testing |

### Decisiones aplicadas
- Broker NATS con JetStream, GHCR, k3s en una VM de Google Cloud: ADR-87 / D-19 (propuesta pendiente de aprobación).
- **Ingress:** Traefik (incluido en k3s), porque ingress-nginx se retiró en marzo de 2026. Detalle y cómo cambiar en `cluster/README.md`.
- **BD de Plataforma:** PostgreSQL 16, como el resto (el directorio de empresas es relacional: subdominio único, estados, dominios).
- El frontend es global: se despliega aparte y no va en el chart por empresa.

### Reglas del monorepo
Trabaja **solo dentro de esta carpeta**. Si necesitas tocar otra, abre un PR separado o coordínate con sus dueños. Guía: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

---

<a name="english"></a>
## English

### Responsibility
**Does:**
- **Local environment** (`local/`): the compose file that brings up the full stack on every team member's machine, plus the `podman kube play` fallback.
- **Testing cluster** (`cluster/`): scripts and runbook for k3s on a Google Cloud VM, with ingress, metrics-server, read-only access per team and a shutdown/startup procedure to control costs.
- **Helm chart** (`helm/stack/`): the reusable template of one company's stack (one service with its own PostgreSQL per file in `services/`, broker, Mailpit, ingress, isolation and quotas).

**Does not:** hold service code, the gateway (`platform/gateway/`) or the frontend. Each team only contributes `helm/stack/services/<their-service>.yaml`.

### Map
See the table above: `local/`, `cluster/` and `helm/stack/` each have their own README (Spanish).

### Commands (from the repository root)
`make up | down | logs | reset | health` (local) · `make kube-build | kube-up | kube-down | kube-reset` (fallback) · `make helm-check` · `make testing-down | testing-up`.

### Decisions applied
NATS with JetStream, GHCR and k3s on a Google Cloud VM (ADR-87 / D-19, proposal pending approval). **Ingress:** Traefik (bundled with k3s) because ingress-nginx was retired in March 2026. Platform DB: PostgreSQL 16. The frontend is global and is deployed separately.

### Monorepo rules
Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../../CONTRIBUTING.en.md).
