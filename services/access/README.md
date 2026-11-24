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
make migrate                # crea las tablas
make seed                   # carga el catálogo de roles
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
| `POST` | `/api/access/v1/login` | Valida credenciales y entrega `acceso` y `refresco`. |
| `POST` | `/api/access/v1/refresh` | Entrega un `acceso` nuevo a partir de un `refresco` válido, enviado en el cuerpo de la petición. |
| `GET` | `/api/docs/` | Documentación navegable (Swagger). |

Ejemplo de inicio de sesión:

```bash
curl -X POST http://localhost:8002/api/access/v1/login \
  -H 'Content-Type: application/json' \
  -d '{"correo": "ana@empresa-demo.mx", "password": "clave-de-prueba-123"}'
```

El token de acceso lleva los claims que declara el contrato:

| Claim | Contenido |
|---|---|
| `sub` | Identificador del usuario. |
| `empresa` | Valor de `EMPRESA_ID`, la empresa dueña del stack. |
| `rol` | Rol del usuario: `administrador`, `agente_n2`, `agente_n1` o `usuario_final`. |
| `permisos` | Permisos efectivos del rol; con esto el frontend dibuja la navegación. |
| `iss` | Emisor del token. |
| `iat` / `exp` | Emisión y expiración; el acceso dura 15 minutos por omisión. |

### Modelos

| Modelo | Para qué |
|---|---|
| `Departamento` | Área de la empresa a la que pertenece un usuario. |
| `Rol` | Catálogo fijo de roles con sus permisos. Se carga con `make seed`. |
| `Usuario` | Persona que entra al help desk. Se identifica por **correo**, no por nombre de usuario. |
| `Perfil` | Datos de la persona que no hacen falta para autenticarla (puesto, teléfono, onboarding). |

Un usuario tiene uno de cuatro estados: `activo`, `invitado` (creado sin contraseña, pendiente de activar), `bloqueado` (por intentos fallidos) y `suspendido` (dado de baja). **Solo un usuario `activo` obtiene token.**

Los permisos no se preguntan por rol sino por permiso (`tickets:ver`, `tickets:atender`, `tickets:escalar`, `empresa:configurar`, `usuarios:administrar`), para que un cambio de roles no rompa a los servicios que los consumen.

### Firma del token

El token se firma con **RS256**. La llave privada vive solo en este servicio y los demás validan con la pública, que se publica en `GET /api/access/v1/.well-known/jwks.json`. Con HS256 habría que repartirles el `SECRET_KEY`, y quien lo tenga no solo verifica tokens: los fabrica.

La llave se toma de `JWT_PRIVATE_KEY`. Para generar una:

```bash
make llaves
```

Imprime la llave en una sola línea, con los saltos escapados, lista para pegarla en el `.env` o en un secreto de Kubernetes. En desarrollo, si la variable está vacía se genera una en `build/jwt-dev.pem`, que no se versiona; se guarda en disco a propósito, porque una llave por proceso daría llaves distintas en cada worker de gunicorn. Fuera de desarrollo, sin esa variable el servicio no arranca.

Cada llave se identifica con un `kid`, que es su huella según el RFC 7638, y los tokens lo llevan en la cabecera para que quien valide sepa cuál aplicar. Al rotar, se publica la llave nueva antes de empezar a firmar con ella.

Si vienes de otro servicio y necesitas validar estos tokens, está todo en [`docs/validar-el-token.md`](docs/validar-el-token.md): la configuración, el fragmento de permisos y cómo comprobarlo.

El contrato de [`contracts/access/openapi.yaml`](../../contracts/access/openapi.yaml) se escribe a mano, porque declara endpoints que este servicio todavía no sirve y que Plataforma y Frontend ya necesitan leer. Para comprobar que el código y el contrato siguen concordando:

```bash
make openapi
```

Genera el esquema desde el código a `build/openapi.generado.yaml`, que no se versiona, y lo compara con el contrato. Nunca escribe sobre el contrato. Falla si el código sirve una operación que el contrato no declara, o si los campos de una respuesta no concuerdan entre los dos.

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
