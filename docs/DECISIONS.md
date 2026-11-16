# Registro de decisiones / Decision log

| ID | Decisión / Decision | Estado / Status |
|---|---|---|
| D-01 | **Monorepo** (reemplaza la decisión inicial de polyrepo, para evitar problemas de coordinación). Los servicios siguen siendo independientes: contenedor, BD y CI propios / **Monorepo** (replaces the initial polyrepo decision to avoid coordination problems). Services stay independent: own container, DB and CI | ✅ Aceptada (cambiada 4-nov-2026) |
| D-02 | **Todos los servicios en Django, frontend en React** (decisión del 14-nov-2026) / **All services in Django, frontend in React** | ✅ Aceptada (cambiada) |
| D-03 | Database per service; cada equipo elige su motor / Database per service; each team picks its engine | ✅ Aceptada |
| D-04 | Subdominio `{empresa}.help-chair.com`; el sitio público vive en `help-chair.com` (reemplaza `helpchair.example`) / Subdomain `{company}.help-chair.com`; the public site lives at `help-chair.com` (replaces `helpchair.example`) | ✅ Aceptada (cambiada 15-nov-2026) |
| D-05 | KB como servicio propio del equipo de Problemas, consumida por API / KB as its own service owned by Problems, consumed via API | ✅ Aceptada |
| D-06 | 7 equipos / 7 teams | ✅ Aceptada |
| D-07 | Broker de mensajes por stack; motor propuesto: NATS / Per-stack message broker; proposed engine: NATS | 🟡 Propuesta (motor por confirmar) |
| D-08 | Namespace de K8s por empresa + NetworkPolicy / K8s namespace per company + NetworkPolicy | 🟡 Propuesta |
| D-09 | Autenticación dentro del stack; directorio global solo mapea usuario/dominio → empresa / Authentication inside the stack; global directory only maps user/domain → company | 🟡 Propuesta |
| D-10 | Change Enablement diferido a fase 2 (lo cubre Peticiones) / Change Enablement deferred to phase 2 (covered by Requests) | 🟡 Propuesta |
| D-11 | Dueño de catálogo de servicios, matriz de prioridad y SLA: Eventos / Owner of service catalogue, priority matrix and SLAs: Events | 🟡 Propuesta |
| D-12 | Framework de frontend / Frontend framework | ✅ Cerrada por D-02 (React + Vite + TypeScript) |
| D-13 | Estrategia de reducción de recursos por stack / Per-stack resource reduction strategy | ⚪ Abierta |
| D-14 | Licencia del proyecto / Project license | ⚪ Abierta |
| D-15 | `CODEOWNERS` por carpeta + CI filtrado por ruta para mantener la independencia de cada equipo / Per-folder `CODEOWNERS` + path-filtered CI to keep each team independent | ✅ Aceptada |
| D-16 | Versionado por servicio con etiquetas `<carpeta>/vX.Y.Z` e imagen `ghcr.io/help-chair/hc-<servicio>` / Per-service versioning with `<folder>/vX.Y.Z` tags and image `ghcr.io/help-chair/hc-<service>` | 🟡 Propuesta |
| D-17 | Contenedores con Podman, orquestación con Kubernetes + Helm, CI/CD con Jenkins, despliegue en nube (Azure, AWS o Google Cloud) / Podman, Kubernetes + Helm, Jenkins, cloud deployment | ✅ Aceptada (nube por elegir) |
| D-18 | Plan de 5 fases de 5 días con ambientes dev / testing / producción; ver `docs/ROADMAP.md` / 5-phase plan with dev / testing / production environments | ✅ Aceptada |
| D-19 | Nube, Kubernetes administrado vs k3s, registro de imágenes y broker (NATS o RabbitMQ) / Cloud, managed Kubernetes vs k3s, image registry and broker | ⚪ Abierta (ver ROADMAP, sección Decisiones pendientes) |
| D-20 | **Alta de empresa con registro mínimo:** el registro pide solo empresa, subdominio y administrador; servicios, SLA, departamentos y usuarios se capturan en el onboarding dentro del stack / **Minimal sign-up (option A):** sign-up asks only company, subdomain and administrator; services, SLAs, departments and users are captured in the in-stack onboarding | ✅ Aceptada (15-nov-2026) |
| D-21 | **Un solo frontend y una sola imagen** para el sitio público (`help-chair.com`) y el Service Desk (`empresaN.help-chair.com`): rutas según el host, `config.json` en tiempo de ejecución y API con rutas relativas `/api` / **One frontend and one image** for the public site and the Service Desk: host-based routes, runtime `config.json`, relative `/api` paths | ✅ Aceptada (15-nov-2026) |
| D-22 | El registro público vive en el gateway de Plataforma (`/api/public/v1`, contrato `contracts/gateway/`); el directorio guarda estado del alta (`pendiente_verificacion`, `aprovisionando`, `activa`, `suspendida`, `error`) y `plan` / Public sign-up lives in Platform's gateway; the directory stores sign-up state and `plan` | 🟡 Propuesta |
| D-23 | El stack **no se aprovisiona hasta verificar el correo** del administrador; límites de uso, nombres reservados y cupo `MAX_TENANTS` / The stack is **not provisioned until the administrator's email is verified**; rate limits, reserved names and `MAX_TENANTS` quota | 🟡 Propuesta |
| D-24 | La contraseña del administrador **nunca** se guarda en la BD global: Accesos crea al administrador sin contraseña y emite un token de activación de un solo uso (se guarda su hash, expira) / The administrator's password is **never** stored in the global DB: Access creates the admin without a password and issues a single-use activation token | 🟡 Propuesta |
| D-25 | El estado del onboarding (`onboarding_completed`) vive en Accesos, en el perfil del administrador / Onboarding state lives in Access, on the administrator's profile | 🟡 Propuesta |
| D-26 | Dominio `help-chair.com` con certificado comodín `*.help-chair.com` (cert-manager, desafío DNS-01); requiere proveedor de DNS con API. Alternativa en testing: nip.io/sslip.io / Domain `help-chair.com` with wildcard certificate (DNS-01); requires a DNS provider with API. Testing fallback: nip.io/sslip.io | ⚪ Abierta (confirmar registro del dominio y proveedor DNS; fecha límite: fase 3, día 1) |
| D-27 | Licencia de pago futura: el directorio incluye el campo `plan` (valor inicial `gratuito`); no se implementa cobro en v1.0.0 / Future paid licence: directory includes a `plan` field (initial value `gratuito`); no billing in v1.0.0 | 🟡 Propuesta |
| D-28 | "Entrar a mi empresa" resuelve por dominio de correo solo para dominios corporativos; proveedores públicos (gmail, outlook…) exigen escribir el subdominio / "Go to my company" resolves by email domain for corporate domains only; public providers require typing the subdomain | 🟡 Propuesta |
