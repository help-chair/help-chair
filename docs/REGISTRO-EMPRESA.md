# Sitio público y registro de empresa

> Decisiones D-20 a D-28 en [`DECISIONS.md`](DECISIONS.md). Flujo y componentes en [`ARCHITECTURE.md`](ARCHITECTURE.md). Contrato en [`../contracts/gateway/openapi.yaml`](../contracts/gateway/openapi.yaml). Plan de entrega en [`ROADMAP.md`](ROADMAP.md).

## 1. Objetivo y alcance

Permitir que una empresa se dé de alta por sí sola desde `help-chair.com` y llegue a su help desk en `empresaN.help-chair.com`, **sin cambiar** los servicios del stack (Eventos, Peticiones, Incidencias, Problemas, KB) ni sus contratos, salvo tres endpoints nuevos en Accesos.

**Opción:** el registro pide lo mínimo. La información detallada (servicios, importancia, SLA, departamentos, usuarios) se captura en el **asistente de onboarding dentro del stack**, que el plan ya contemplaba en la fase 3.

**Fuera de alcance de v1.0.0:** cobro y licencias (solo el campo `plan`), CAPTCHA, SSO en el registro, edición de la empresa desde el sitio público.

## 2. Qué se pide y dónde

| Momento | Datos | Dónde se guardan |
|---|---|---|
| Registro (sitio público) | Nombre de la empresa, subdominio, nombre y correo del administrador, aceptar términos. Opcionales: sector, tamaño (rango), país | Directorio global (Plataforma) |
| Activación | Contraseña del administrador | Solo dentro del stack (Accesos), con hash. **Nunca** en el directorio |
| Onboarding (primer ingreso) | Servicios e importancia, prioridades, SLA, departamentos, roles y usuarios | Servicios del stack: Eventos (catálogo, SLA), Accesos (usuarios, roles) |

## 3. Estados de la empresa

```
pendiente_verificacion ──(correo verificado)──► aprovisionando ──(stack listo)──► activa
        │                                              │                            │
   (expira 24 h)                                  (falla)                     suspendida ◄─► activa
        ▼                                              ▼
     eliminada                                       error ──(reintento manual)──► aprovisionando
```

- Una solicitud no verificada en 24 h se elimina y libera el subdominio.
- `error` guarda el motivo en el directorio; el reintento es manual (`make tenant-retry EMPRESA=<subdominio>` o job parametrizado de Jenkins, ver runbook `alta-empresa.md`).

## 4. API pública (resumen; ver OpenAPI)

| Método y ruta | Uso |
|---|---|
| `GET /subdomains/{subdominio}/availability` | Disponibilidad en tiempo real mientras se escribe |
| `POST /companies` | Crea la solicitud (202) y envía el correo de verificación |
| `POST /companies/verify` | Verifica el correo e inicia el aprovisionamiento (es POST para que los escáneres de enlaces no lo ejecuten) |
| `GET /companies/{id}/status` | Pantalla de progreso; requiere `X-Tracking-Token` |
| `POST /lookup` | "Entrar a mi empresa": correo → subdominio (solo dominios corporativos) |

## 5. Endpoints nuevos en Accesos (propuesta para `contracts/access/` v0)

El equipo de Accesos los incorpora a su OpenAPI **antes de congelar `contracts-v1`** (cierre de la fase 2).

| Endpoint | Quién lo llama | Descripción |
|---|---|---|
| `POST /internal/v1/bootstrap-admin` | Aprovisionador | Cuerpo `{nombre, correo}`. Crea al administrador **sin contraseña** y responde 201 `{usuario_id, token_activacion, expira_en}`. Si ya existe un administrador responde 409 (idempotencia). Autenticado con `Authorization: Bearer <PROVISIONER_TOKEN>` (secreto por stack). **No se expone en el ingress**; solo alcanzable desde el aprovisionador (NetworkPolicy) |
| `POST /api/access/v1/activate` | Frontend (`/activar`) | Cuerpo `{token, password}`. Valida token (un solo uso, 72 h, se guarda su hash), aplica la política de contraseñas y responde 204. 400 si el token es inválido, usado o expirado |
| `GET /api/access/v1/me` y `PATCH /api/access/v1/me/onboarding` | Frontend | `me` incluye `onboarding_completed`; el `PATCH` (`{completed: true}`) lo marca al terminar el asistente. Solo rol administrador |

La **invitación de usuarios por correo** (fase 4, ya planeada) reutiliza el mismo mecanismo de token y `activate`.

## 6. Directorio de empresas (modelo propuesto)

| Campo | Notas |
|---|---|
| `id` (uuid), `nombre`, `subdominio` (único) | |
| `estado`, `error_detalle` | Ver sección 3 |
| `plan` | `gratuito` por ahora (D-27) |
| `nombre_admin`, `correo_admin` | Solo para el correo y el aprovisionamiento |
| `dominios_correo` | Lista; se llena con el dominio del administrador si es corporativo (D-28) |
| `sector`, `tamano`, `pais` | Opcionales, solo informativos |
| `token_verificacion_hash`, `token_seguimiento_hash`, `verificado_en` | Solo hashes |
| `creado_en`, `actualizado_en` | |

## 7. Seguridad del registro

- **Verificación de correo antes de aprovisionar:** sin correo verificado no se crea ningún namespace.
- **Límites de uso** (DRF throttling, valores iniciales por IP): disponibilidad 30/min, alta 5/h, verificación 10/h, lookup 10/min. Responden 429 con `Retry-After`.
- **Cupo `MAX_TENANTS`:** al alcanzarlo, el alta responde "lista de espera" sin crear el stack.
- **Subdominios:** regex `^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$`, lista de reservados (`www`, `api`, `admin`, `app`, `mail`, `status`, `help`, `support`…) y unicidad sin distinguir mayúsculas.
- **Tokens:** 32 bytes aleatorios (urlsafe), se almacena solo el hash, un solo uso; verificación 24 h, activación 72 h.
- **Sin enumeración:** `status` devuelve 404 igual para id inexistente o token incorrecto; `lookup` responde igual si el dominio no existe.
- **Secretos por stack:** `PROVISIONER_TOKEN` se crea al aprovisionar y vive solo en el namespace de la empresa y en el aprovisionador.
- **Pruebas:** ZAP baseline y k6 incluyen los endpoints públicos (fase 4).

## 8. Frontend

| Dominio | Rutas |
|---|---|
| `help-chair.com` | `/` landing, `/registro`, `/verificar?token=`, `/estado/:id`, `/entrar` |
| `empresaN.help-chair.com` | `/activar?token=` y el Service Desk (dashboard; el asistente de onboarding se muestra al primer ingreso del administrador) |

- El enrutado por host se decide al arrancar con `window.location.hostname` y el `BASE_DOMAIN` de `/config.json` (`frontend/src/config/runtime.ts`).
- `config.json` lo genera el contenedor al iniciar (`frontend/docker/40-hc-config.sh`, a partir de la variable `BASE_DOMAIN`) y se sirve con `Cache-Control: no-store`. Así la misma imagen sirve a todos los ambientes.
- La URL de la API deja de incrustarse al construir (`VITE_API_BASE_URL`): el cliente usa `/api/...` y, en desarrollo, el proxy de Vite.
- Los dos conjuntos de rutas se cargan con *lazy loading* para que el sitio público no pese en el Service Desk y viceversa.
- Redirección al terminar: al ver `activa`, el progreso lleva a `url` (el subdominio) y de ahí a `/activar`.

## 9. Degradaciones (plan B)

| Si falla | Entonces |
|---|---|
| SMTP real no disponible | `PUBLIC_SHOW_ACTIVATION_LINK=true`: el enlace de activación se muestra **una sola vez** en la pantalla de progreso del navegador que hizo el registro. Se pierde la verificación de correo; solo para demostración |
| Aprovisionamiento automático complicado | Semiautomático: la solicitud queda en `aprovisionando` y Plataforma ejecuta `make tenant-create EMPRESA=...` con los datos del directorio; el resto del flujo no cambia |
| Certificado comodín (DNS-01) no disponible | Certificado por subdominio con HTTP-01 bajo demanda (límites de Let's Encrypt) o autofirmado en testing |
| Falta tiempo en el frontend | Ver orden de recorte en `ROADMAP.md` |

---

## English summary

**Goal:** companies sign themselves up at `help-chair.com` and land on `companyN.help-chair.com`, **without changing** the stack services (Events, Requests, Incidents, Problems, KB), except three new Access endpoints.

**Option A:** sign-up asks only for company, subdomain and administrator. Detailed information (services, importance, SLAs, departments, users) is captured by the **in-stack onboarding wizard** already planned for phase 3.

**Flow:** register → verification email (`pendiente_verificacion`) → verify (`aprovisionando`) → provisioner creates the stack and asks Access for the initial admin *without a password* → activation link by email (`activa`) → admin sets a password inside the stack → onboarding.

**Key rules:** no stack before email verification; the admin password never reaches the global directory; single-use hashed tokens; rate limits and a `MAX_TENANTS` quota; one frontend image with host-based routes and a runtime `config.json`; relative `/api` paths. API contract: `contracts/gateway/openapi.yaml`. Plan and dates: `ROADMAP.md`.
