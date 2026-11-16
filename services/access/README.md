# services/access

[English below ↓](#english)

> Gestión de Accesos: usuarios, roles, autenticación y eventos de credenciales. / Access Management: users, roles, authentication and credential events.

| | |
|---|---|
| **Equipo / Team** | Gestión de Accesos / Access Management |
| **Práctica ITIL v4 / ITIL v4 practice** | Service Request Mgmt + Information Security Mgmt |
| **Imagen / Image** | `ghcr.io/help-chair/hc-access` |
| **Contratos / Contracts** | `contracts/access/openapi.yaml`, `contracts/messages/access-eventos-seguridad.yaml` |
| **Puerto / Port** | `8002` (BD local en `5442`) |

## Español

### Responsabilidad

**Qué hace esta carpeta:**

- Guarda los usuarios del stack, sus departamentos, sus roles y sus perfiles de permisos.
- Autentica: valida credenciales y emite el token JWT con el que los demás servicios reconocen a quien llama.
- Publica eventos de seguridad (inicios de sesión, bloqueos, cambios de rol) para que Gestión de Eventos los clasifique.

**Qué NO hace:**

- No sabe nada de tickets, incidencias, peticiones ni problemas.
- No lee la base de datos de ningún otro servicio ni expone la suya.
- No resuelve a qué empresa pertenece un usuario: cada empresa tiene su propio stack, y la empresa llega como configuración (`EMPRESA_ID`).

### Stack tecnológico

- Lenguaje / framework: Python 3.12 / Django 5 + Django REST Framework
- Autenticación: `djangorestframework-simplejwt`
- Base de datos: PostgreSQL 16 propia del servicio (SQLite en local si no se define `DATABASE_URL`)
- OpenAPI: `drf-spectacular`

### Ejecución local

```bash
cd services/access
make setup                  # crea .env y el entorno virtual
make test                   # pruebas con cobertura
make run                    # http://localhost:8002
```

Con eso corre sobre SQLite, suficiente para desarrollar y para `make test`. Para trabajar contra PostgreSQL, levanta la base del compose y descomenta `DATABASE_URL` en tu `.env`:

```bash
docker compose -f ../../platform/deploy/local/compose.yaml up -d access-db
make migrate && make run
```

Comprobación rápida:

```bash
curl http://localhost:8002/health/ready
```

### API

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/health/live` | El proceso responde. |
| `GET` | `/health/ready` | El proceso responde y la base es alcanzable. |
| `POST` | `/api/auth/login` | Valida credenciales y entrega `access` y `refresh`. |
| `POST` | `/api/auth/refresh` | Entrega un `access` nuevo a partir de un `refresh` válido. |
| `GET` | `/api/docs/` | Documentación navegable (Swagger). |

Ejemplo de inicio de sesión:

```bash
curl -X POST http://localhost:8002/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "ana", "password": "clave-de-prueba-123"}'
```

El token de acceso lleva los claims que exige el plan:

| Claim | Contenido |
|---|---|
| `empresa` | Valor de `EMPRESA_ID`, la empresa dueña del stack. |
| `rol` | Rol del usuario. |
| `exp` | Expiración, por omisión 15 minutos. |

Para exportar el contrato después de cambiar la API:

```bash
make openapi
```

### Variables de entorno

Las define `.env.example`. Las que importan:

| Variable | Para qué | Por omisión |
|---|---|---|
| `SECRET_KEY` | Clave de Django. Obligatoria fuera de desarrollo. | — |
| `DEBUG` | Modo desarrollo. | `false` |
| `PORT` | Puerto del servidor. | `8002` |
| `EMPRESA_ID` | Empresa del stack; va en el claim `empresa`. | `empresa-demo` |
| `ACCESS_TOKEN_MINUTOS` | Vigencia del token de acceso. | `15` |
| `REFRESH_TOKEN_DIAS` | Vigencia del token de refresco. | `1` |
| `DATABASE_URL` | Base del servicio. Sin ella se usa SQLite. | — |

### Eventos que emite

El catálogo vive en [`contracts/messages/access-eventos-seguridad.yaml`](../../contracts/messages/access-eventos-seguridad.yaml): inicios de sesión exitosos y fallidos, bloqueo de cuenta, cambio de contraseña, alta de usuario y cambio de rol. La publicación al broker entra en la fase 2.

### Reglas del monorepo

Trabaja **solo dentro de esta carpeta**. Si necesitas tocar otra, abre un PR separado o coordínate con sus dueños. Guía: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

---

<a name="english"></a>

## English

### Responsibility

**What this folder does:** stores the stack's users, departments, roles and permission profiles; authenticates credentials and issues the JWT other services trust; publishes security events for Event Management.

**What it does NOT do:** it knows nothing about tickets, never reads another service's database, and does not resolve which company a user belongs to — each company runs its own stack and the company arrives as configuration (`EMPRESA_ID`).

### Tech stack

Python 3.12 / Django 5 + Django REST Framework, `djangorestframework-simplejwt`, PostgreSQL 16 (SQLite locally when `DATABASE_URL` is unset), OpenAPI via `drf-spectacular`.

### Running locally

```bash
cd services/access
make setup && make test && make run   # http://localhost:8002
```

See the Spanish section above for the endpoint table, token claims and environment variables.

### Monorepo rules

Work **only inside this folder**. If you must change another one, open a separate PR or coordinate with its owners. Guide: [`CONTRIBUTING.en.md`](../../CONTRIBUTING.en.md).
