# frontend

[English below ↓](#english)

> Frontend de Help Chair: **sitio público** (`help-chair.com`: landing, registro de empresa, entrar a mi empresa) y **Service Desk** (`empresaN.help-chair.com`): punto único de contacto (SPOC) y Dashboard operacional de eventos, incidentes, peticiones y problemas. Una sola SPA y una sola imagen. / Help Chair frontend: **public site** (landing, company sign-up, go to my company) and **Service Desk** (single point of contact and operational dashboard). One SPA, one image.

| | |
|---|---|
| **Equipo / Team** | Frontend (Equipo 6) |
| **Práctica ITIL v4 / ITIL v4 practice** | Service Desk |
| **Imagen / Image** | `ghcr.io/help-chair/hc-frontend` |
| **Contratos / Contracts** | `contracts/` (sitio público: `contracts/gateway/`) |
| **Guía de Despliegue / Ops Guide** | [`DEPLOYMENT.md`](DEPLOYMENT.md) |
| **Diseño y Figma / UI Guide** | [`DESIGN.md`](DESIGN.md) |
| **Diseño del registro / Sign-up design** | [`../docs/REGISTRO-EMPRESA.md`](../docs/REGISTRO-EMPRESA.md) |

---

## Español

### Responsabilidad
- **Qué hace esta carpeta:**
  - Implementa la interfaz SPA del Service Desk para agentes y administradores de la empresa.
  - Ofrece el **Dashboard principal**, funcionando como centro de mando y visualizador del flujo de eventos (Monitoring Feed) generado por `services/events`.
  - Proporciona navegación y acceso unificado hacia los microservicios de Incidencias, Peticiones, Problemas y Base de Conocimiento.
  - Maneja la visualización de SLAs y estado de los servicios.
  - Implementa el **sitio público**: landing, registro de empresa, verificación de correo, progreso del alta y «Entrar a mi empresa».
  - Implementa la **activación de la cuenta del administrador** (`/activar`) en el subdominio de la empresa.
  - Implementa el **inicio de sesión del Service Desk** y la **navegación según el rol** de la sesión (RBAC), más la pantalla de **Gestión de Accesos** (usuarios, roles, bloqueos) contra `services/access`.
- **Qué NO hace esta carpeta:**
  - No gestiona base de datos propia ni persiste tickets directamente (cada microservicio backend es dueño de su BD).
  - No procesa reglas de negocio complejas en el cliente; consume las APIs y contratos definidos en `contracts/`.
  - No guarda contraseñas ni datos de la empresa: el registro y la activación viven en Plataforma y Accesos.

### Sitio público y Service Desk en una sola imagen
Al arrancar, la SPA decide qué mostrar según el dominio (`src/config/runtime.ts`):

| Dominio | Qué muestra | Rutas |
|---|---|---|
| `help-chair.com` (el `BASE_DOMAIN`) | Sitio público | `/`, `/registro`, `/verificar?token=`, `/estado/:id`, `/entrar` |
| `empresaN.help-chair.com` | Service Desk | `/` (dashboard) y `/activar?token=` |
| Host desconocido | Desarrollo: Service Desk · Producción: sitio público | — |

- **Configuración de tiempo de ejecución:** el contenedor genera `/config.json` al arrancar con `BASE_DOMAIN`. No hay URLs ni dominios incrustados al compilar.
- **API con rutas relativas** (`/api/...`): en desarrollo las reenvía el proxy de Vite (`vite.config.ts`); en producción, el gateway/ingress según el `Host`. No hay CORS.
- **Carga diferida:** el sitio público, la activación y el Service Desk son bloques separados.
- **Enrutador propio** (`src/lib/routing.ts`, sin dependencias nuevas). Para pantallas nuevas del sitio público agrega la ruta en `features/public/PublicSite.tsx`.
- En desarrollo cambia de sitio sin tocar DNS: `http://localhost:5173/?site=public` (o `?site=desk`).

### Stack tecnológico
- **Lenguaje y runtime:** TypeScript / Node.js 20+
- **Framework frontend:** React 19 + Vite 6
- **Estilos y Componentes:** Tailwind CSS + Lucide React (arquitectura orientada a shadcn/ui)
- **Testing y Calidad:** Vitest + Testing Library + ESLint 9 + Prettier
- **Servidor web de producción:** Nginx unprivileged (imagen Alpine no-root)

### Contrato mínimo de servicio
- [x] `Dockerfile` multi-stage y usuario no root (UID 101)
- [x] `GET /health/live` y `GET /health/ready` (respuestas JSON vía Nginx)
- [x] Configuración solo por variables de entorno (`BASE_DOMAIN` al arrancar; `.env.example` para desarrollo)
- [ ] Logs en JSON
- [x] Consumo de contratos OpenAPI documentados en `contracts/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-frontend`
- [x] `requests`/`limits` de recursos declarados (detallados en [`DEPLOYMENT.md`](DEPLOYMENT.md))
- [x] Cierre ordenado con `SIGTERM`
- [x] Workflow de CI propio, filtrado por esta ruta (ver `../CONTRIBUTING.md`)

### Ejecución local

#### Opción A: Con Docker (Recomendado para el equipo con Hot-Reloading)
Permite levantar el entorno de desarrollo idéntico para todos los integrantes sin requerir instalar Node en el host:
```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up
```
Abre en tu navegador: [http://localhost:5173](http://localhost:5173). Cualquier cambio en el código se reflejará al instante. Con Podman, usa `podman compose` y cambia `host.docker.internal` por `host.containers.internal` en el archivo.

#### Opción B: Ejecución directa con Node/npm
```bash
cp .env.example .env
npm install
npm run dev
```

#### Conectar con los backends
El frontend ya no usa servidores de mocks (Prism) ni datos simulados: todas las pantallas llaman a
los microservicios reales con rutas relativas (`/api/<servicio>/v1/...`). En local, levanta los
servicios que necesites (`make up` en `platform/deploy/local/` o `make run` en cada
servicio) y el proxy de Vite reenvía cada prefijo al puerto de la tabla de abajo, sin reescribir
la ruta, igual que el ingress del clúster de testing.

Si un servicio no responde, la pantalla lo dice y ofrece **Reintentar**. Cada petición se corta a
los 15 s (`TIEMPO_LIMITE_MS` en `src/api/client.ts`).

### Variables de Entorno

**Desarrollo (`.env`).** Son los destinos del proxy de Vite; el cliente no los lee:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `VITE_API_GATEWAY_URL` | Gateway (API pública de registro) | `http://localhost:8000` |
| `VITE_API_EVENTS_URL` | Microservicio de Eventos | `http://localhost:8001` |
| `VITE_API_ACCESS_URL` | Microservicio de Accesos | `http://localhost:8002` |
| `VITE_API_REQUESTS_URL` | Microservicio de Peticiones | `http://localhost:8003` |
| `VITE_API_INCIDENTS_URL` | Microservicio de Incidencias | `http://localhost:8004` |
| `VITE_API_PROBLEMS_URL` | Microservicio de Problemas | `http://localhost:8005` |
| `VITE_API_KNOWLEDGE_URL` | Base de Conocimiento | `http://localhost:8006` |
| `VITE_DEV_TENANT_ID` | Identificador de empresa en local | `empresa-demo` |

**Producción (al arrancar el contenedor):**

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `BASE_DOMAIN` | Dominio base (`help-chair.com`); define qué hosts son sitio público y cuáles son empresas | `localhost` |

### 🤖 Guía para Desarrolladores y Agentes de IA
Al generar o modificar código en este frontend:
1. **Componentes reutilizables:** Utiliza exclusivamente Tailwind CSS y la estructura modular en `src/components/ui/`. Evita instalar librerías pesadas adicionales.
2. **Vocabulario ITIL v4 estricto:**
   - Eventos: *Informativo*, *Advertencia*, *Excepción*.
   - Tickets: *Incidencias*, *Peticiones de Servicio*, *Problemas*.
   - Prioridad calculada por *Impacto × Urgencia*.
3. **Consumo de contratos:** Toda llamada a endpoints debe respetar los esquemas de `contracts/`.
4. **Rutas y dominios:** ver las reglas de la sección 6 de [`AGENTS.md`](AGENTS.md).

### Despliegue en Producción
Para desplegar el contenedor en producción o integrarlo con Kubernetes, consulta la [Guía de Despliegue (`DEPLOYMENT.md`)](DEPLOYMENT.md).

### Reglas del monorepo
Trabaja **solo dentro de esta carpeta**. Si necesitas tocar otra, abre un PR separado o coordínate con sus dueños. Guía: [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

<a name="english"></a>
## English

### Responsibility
- **What this folder does:**
  - Implements the Service Desk SPA for enterprise agents and administrators.
  - Hosts the **Main Dashboard**, serving as the operational command centre and monitoring feed visualizer generated by `services/events`.
  - Provides unified navigation and entry point to Incidents, Requests, Problems, and Knowledge Base microservices.
  - Displays SLAs and service health metrics.
  - Implements the **public site**: landing, company sign-up, email verification, sign-up progress and "Go to my company".
  - Implements the **administrator account activation** (`/activar`) on the company's subdomain.
- **What this folder does NOT do:**
  - Does not manage an internal database or persist tickets directly (each backend service owns its DB).
  - Does not execute complex business rules on the client; consumes contracts defined in `contracts/`.
  - Does not store passwords or company data: sign-up and activation live in Platform and Access.

### Public site and Service Desk in one image
On start-up the SPA picks what to show from the domain (`src/config/runtime.ts`):

| Domain | Shows | Routes |
|---|---|---|
| `help-chair.com` (the `BASE_DOMAIN`) | Public site | `/`, `/registro`, `/verificar?token=`, `/estado/:id`, `/entrar` |
| `companyN.help-chair.com` | Service Desk | `/` (dashboard) and `/activar?token=` |
| Unknown host | Development: Service Desk · Production: public site | — |

- **Runtime configuration:** the container generates `/config.json` on start with `BASE_DOMAIN`. No URL or domain is baked in at build time.
- **Relative API paths** (`/api/...`): the Vite proxy forwards them in development; the gateway/ingress does it in production by `Host`. No CORS.
- **Lazy loading:** public site, activation and Service Desk are separate chunks.
- In development switch sites without DNS: `http://localhost:5173/?site=public` (or `?site=desk`).

### Tech stack
- **Language / runtime:** TypeScript / Node.js 20+
- **Frontend framework:** React 19 + Vite 6
- **Styling & Components:** Tailwind CSS + Lucide React (shadcn/ui compatible)
- **Testing & Quality:** Vitest + Testing Library + ESLint 9 + Prettier
- **Production web server:** Nginx unprivileged (Alpine non-root image)

### Minimum service contract
See the checklist in the Spanish section above.

### Running locally

#### Option A: With Docker (Recommended for team with Hot-Reloading)
```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up
```
Open [http://localhost:5173](http://localhost:5173). With Podman use `podman compose` and replace `host.docker.internal` with `host.containers.internal` in the file.

#### Option B: Direct with Node/npm
```bash
cp .env.example .env
npm install
npm run dev
```

#### Connect to the backends
There are no mock servers (Prism) or simulated data: every screen calls the real microservices
through relative paths (`/api/<service>/v1/...`). Start the services you need locally; the Vite
proxy forwards each prefix without rewriting the path, just like the testing cluster ingress.

### Production Deployment
See [`DEPLOYMENT.md`](DEPLOYMENT.md) for Docker Compose and Kubernetes instructions. Production configuration is a single variable, `BASE_DOMAIN`, read when the container starts.

### Monorepo rules
Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../CONTRIBUTING.en.md).
