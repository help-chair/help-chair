# platform/gateway

[English below ↓](#english)

> Gateway de subdominio, registro público de empresas y directorio de empresas (tenants). / Subdomain gateway, public company sign-up and company (tenant) directory.

| | |
|---|---|
| **Equipo / Team** | Plataforma / Platform |
| **Práctica ITIL v4 / ITIL v4 practice** | Platform and Deployment |
| **Imagen / Image** | `ghcr.io/help-chair/hc-platform-gateway` |
| **Contratos / Contracts** | `contracts/` |

## Español

### Responsabilidad
**Hace:**
- Resuelve la empresa a partir del `Host` (`empresaN.help-chair.com`) y enruta al stack correcto.
- Expone la **API pública de registro** (`/api/public/v1`, contrato en `contracts/gateway/`): disponibilidad de subdominio, alta, verificación de correo, estado del alta y búsqueda de empresa por correo.
- Mantiene el **directorio de empresas**: estado del alta (`pendiente_verificacion`, `aprovisionando`, `activa`, `suspendida`, `error`), `plan`, dominios de correo y metadatos básicos.
- Envía los correos de verificación y activación y pide el aprovisionamiento del stack al verificar el correo.
- Aplica límites de uso, nombres reservados y el cupo `MAX_TENANTS`.

**No hace:** no autentica usuarios ni guarda contraseñas (lo hace Accesos dentro del stack) y no guarda la configuración del help desk (servicios, SLA, usuarios).

Diseño completo: [`docs/REGISTRO-EMPRESA.md`](../../docs/REGISTRO-EMPRESA.md).

### Stack tecnológico
- Lenguaje / framework: Python / Django (D-02)
- Base de datos: PostgreSQL (directorio de empresas, propia de este servicio)

### Contrato mínimo de servicio
- [ ] `Dockerfile` y usuario no root
- [ ] `GET /health/live` y `GET /health/ready`
- [ ] Configuración solo por variables de entorno (`.env.example`)
- [ ] Logs en JSON
- [ ] API documentada con OpenAPI en `contracts/`; eventos según `contracts/messages/`
- [ ] Imagen publicada en `ghcr.io/help-chair/hc-platform-gateway`
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
**Does:**
- Resolves the company from the `Host` (`companyN.help-chair.com`) and routes to the right stack.
- Exposes the **public sign-up API** (`/api/public/v1`, contract in `contracts/gateway/`): subdomain availability, sign-up, email verification, sign-up status and company lookup by email.
- Maintains the **company directory**: sign-up state, `plan`, email domains and basic metadata.
- Sends verification and activation emails and requests stack provisioning once the email is verified.
- Applies rate limits, reserved names and the `MAX_TENANTS` quota.

**Does not:** authenticate users or store passwords (Access does that inside the stack) or store help desk configuration (services, SLAs, users).

Full design: [`docs/REGISTRO-EMPRESA.md`](../../docs/REGISTRO-EMPRESA.md) (Spanish).

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
