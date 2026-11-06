# Arquitectura / Architecture

*Español primero, English below.*

---

## 🇪🇸 Español

### 1. Componentes

| Componente | Alcance | Dueño | Descripción |
|---|---|---|---|
| Frontend | Global | Equipo 6 | SPA del Service Desk. Framework por definir. |
| Gateway de subdominio | Global | Equipo 7 | Resuelve la empresa a partir del subdominio/usuario y enruta al stack correcto. |
| BD de empresas | Global | Equipo 7 | Directorio de *tenants*: empresa, subdominio, estado del stack. |
| Aprovisionador | Global | Equipo 7 | Crea el stack (namespace, manifiestos/Helm) de cada empresa nueva. |
| Gateway de Eventos | Por stack | Equipo 1 | Punto de entrada del stack; recibe, filtra, clasifica, prioriza y enruta eventos. |
| Accesos | Por stack | Equipo 2 | Usuarios, roles, autenticación y eventos de credenciales. |
| Peticiones | Por stack | Equipo 3 | Solicitudes estándar del catálogo. |
| Incidencias | Por stack | Equipo 4 | Fallas y degradaciones de servicio. |
| Problemas | Por stack | Equipo 5 | Causa raíz, patrones repetidos, errores conocidos. |
| Base de Conocimiento (KB) | Por stack | Equipo 5 | Soluciones y artículos; se consume por API (Eventos, Incidencias, Problemas). |
| Broker de mensajes | Por stack | Equipo 7 (infra) | Mensajería asíncrona entre servicios (propuesto: NATS). |

**Ubicación en el monorepo:** Frontend → `frontend/`; Gateway y BD de empresas → `platform/gateway/`; Aprovisionador → `platform/deploy/`; Eventos, Accesos, Peticiones, Incidencias, Problemas y KB → `services/<nombre>/`.

### 2. Ciclo de vida de una empresa

1. **Alta:** se registra en la BD de empresas con su subdominio.
2. **Aprovisionamiento:** el aprovisionador crea un namespace con todos los contenedores y BD vacías.
3. **Login:** el usuario entra al sitio principal; el directorio de empresas resuelve su subdominio y el gateway redirige a `empresaN.helpchair.example`.
4. **Autenticación:** la realiza el servicio de Accesos **dentro del stack** (el directorio global solo guarda el mapeo usuario/dominio → empresa).
5. **Onboarding:** el primer usuario (administrador) configura servicios y su importancia, prioridades, SLA, departamentos, roles y usuarios.
6. **Operación:** el stack procesa eventos, peticiones, incidentes y problemas.

### 3. Aislamiento

- Un **namespace de Kubernetes por empresa**.
- **NetworkPolicy** que bloquea todo tráfico entre namespaces; solo el gateway global puede entrar a cada stack.
- Secretos y credenciales de BD **por stack**.
- Ningún servicio de un stack conoce direcciones de otro stack.

### 4. Comunicación interna

- **Síncrona (REST):** consultas puntuales (p. ej. Eventos → KB para auto-respuesta).
- **Asíncrona (broker):** propagación de eventos (p. ej. Eventos → Incidencias; Accesos → Eventos; Incidencias → Problemas).
- Todos los endpoints y mensajes se definen en `contracts/` y se versionan con SemVer.
- Dirección de dependencias: **Eventos → (Peticiones, Incidencias, Problemas)**; **Accesos → Eventos**; **Problemas consume Incidencias** (no al revés); **KB es consultada** por Eventos, Incidencias y Problemas.

### 5. Flujo de un evento (resumen de las 9 reglas del equipo de Eventos)

| # | Condición | Destino |
|---|---|---|
| 1 | Evento de sistema, informativo, sin acción requerida | Solo registro (cierre automático) |
| 2 | Disparado por usuario, existe solución en KB, dificultad fácil | Auto-respuesta + encuesta (si no resuelve, sigue) |
| 3 | Advertencia bajo el umbral de recurrencia | Registro y vigilancia; alerta si supera el umbral |
| 4 | Seguridad o credenciales | Accesos / Seguridad |
| 5 | Solicitud estándar del catálogo | Peticiones |
| 6 | Falla, degradación o interrupción | Incidencias |
| 7 | Patrón repetido N veces en T días, o causa raíz desconocida | Problemas |
| 8 | Requiere modificar configuración/infraestructura | Cambios (absorbido por Peticiones en el MVP) |
| 9 | Ninguna coincide | Triage manual |

Estados de ciclo de vida: Nuevo → Asignado → En proceso ⇄ En espera → Resuelto → Cerrado; además Rechazado, Cancelado y Reabierto.

### 6. Responsabilidad de configuración (propuesta, por confirmar)

| Configuración | Dueño |
|---|---|
| Usuarios, roles, perfiles, departamentos, grupos | Accesos |
| Catálogo de servicios, importancia, matriz de prioridad, SLA | Eventos (expone por API) |
| Metadatos de la empresa (nombre, subdominio, estado) | Plataforma |
| Formularios de onboarding | Frontend (consume las APIs anteriores) |

### 7. Optimización de recursos

- Imágenes mínimas (Alpine / distroless / multi-stage).
- `requests`/`limits` de CPU y RAM por contenedor y `ResourceQuota` por namespace.
- Escalado a cero / hibernación de stacks inactivos (p. ej. KEDA).
- Distribución ligera de Kubernetes (k3s) en desarrollo.
- Broker ligero (NATS) y pocos contenedores auxiliares.

---

## 🇬🇧 English

### 1. Components

| Component | Scope | Owner | Description |
|---|---|---|---|
| Frontend | Global | Team 6 | Service Desk SPA. Framework TBD. |
| Subdomain gateway | Global | Team 7 | Resolves the company from subdomain/user and routes to the right stack. |
| Companies DB | Global | Team 7 | Tenant directory: company, subdomain, stack status. |
| Provisioner | Global | Team 7 | Creates each new company's stack (namespace, manifests/Helm). |
| Event Gateway | Per stack | Team 1 | Stack entry point; receives, filters, classifies, prioritises and routes events. |
| Access | Per stack | Team 2 | Users, roles, authentication and credential events. |
| Requests | Per stack | Team 3 | Standard catalogue requests. |
| Incidents | Per stack | Team 4 | Service failures and degradations. |
| Problems | Per stack | Team 5 | Root cause, recurring patterns, known errors. |
| Knowledge Base (KB) | Per stack | Team 5 | Solutions and articles; consumed via API (Events, Incidents, Problems). |
| Message broker | Per stack | Team 7 (infra) | Asynchronous messaging between services (proposed: NATS). |

**Location in the monorepo:** Frontend → `frontend/`; Gateway and Companies DB → `platform/gateway/`; Provisioner → `platform/deploy/`; Events, Access, Requests, Incidents, Problems and KB → `services/<name>/`.

### 2. Company lifecycle

1. **Sign-up:** registered in the Companies DB with its subdomain.
2. **Provisioning:** the provisioner creates a namespace with all containers and empty DBs.
3. **Login:** the user visits the main site; the directory resolves their subdomain and the gateway redirects to `companyN.helpchair.example`.
4. **Authentication:** performed by the Access service **inside the stack** (the global directory only stores user/domain → company mapping).
5. **Onboarding:** the first user (admin) configures services and their importance, priorities, SLAs, departments, roles and users.
6. **Operation:** the stack processes events, requests, incidents and problems.

### 3. Isolation

- One **Kubernetes namespace per company**.
- **NetworkPolicy** blocking all cross-namespace traffic; only the global gateway may enter each stack.
- Database secrets and credentials **per stack**.
- No service in a stack knows another stack's addresses.

### 4. Internal communication

- **Synchronous (REST):** point queries (e.g. Events → KB for auto-reply).
- **Asynchronous (broker):** event propagation (e.g. Events → Incidents; Access → Events; Incidents → Problems).
- All endpoints and messages live in `contracts/`, versioned with SemVer.
- Dependency direction: **Events → (Requests, Incidents, Problems)**; **Access → Events**; **Problems consumes Incidents** (not the reverse); **KB is queried** by Events, Incidents and Problems.

### 5. Event flow (summary of Team 1's 9 rules)

| # | Condition | Destination |
|---|---|---|
| 1 | System event, informational, no action required | Log only (auto-close) |
| 2 | User-triggered, solution exists in KB, easy difficulty | Auto-reply + survey (if unresolved, continue) |
| 3 | Warning under recurrence threshold | Log & watch; alert if threshold exceeded |
| 4 | Security or credentials | Access / Security |
| 5 | Standard catalogue request | Requests |
| 6 | Failure, degradation or outage | Incidents |
| 7 | Same pattern N times in T days, or unknown root cause | Problems |
| 8 | Requires configuration/infrastructure change | Changes (absorbed by Requests in the MVP) |
| 9 | None match | Manual triage |

Lifecycle states: New → Assigned → In progress ⇄ On hold → Resolved → Closed; plus Rejected, Cancelled and Reopened.

### 6. Configuration ownership (proposal, to be confirmed)

| Configuration | Owner |
|---|---|
| Users, roles, profiles, departments, groups | Access |
| Service catalogue, importance, priority matrix, SLAs | Events (exposed via API) |
| Company metadata (name, subdomain, status) | Platform |
| Onboarding forms | Frontend (consumes the APIs above) |

### 7. Resource optimisation

- Minimal images (Alpine / distroless / multi-stage).
- CPU/RAM `requests`/`limits` per container and a `ResourceQuota` per namespace.
- Scale-to-zero / hibernating idle stacks (e.g. KEDA).
- Lightweight Kubernetes (k3s) for development.
- Lightweight broker (NATS) and few auxiliary containers.
