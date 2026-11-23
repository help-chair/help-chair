# Guía de entorno de desarrollo

## Requisitos
| Herramienta | Para qué | ¿Obligatoria? |
|---|---|---|
| Git, Make | Flujo de trabajo y atajos | Sí |
| Python 3.12 | Backend | Sí (uv puede instalarlo por ti) |
| [uv](https://docs.astral.sh/uv/) | Dependencias y entornos | **Recomendada**, no obligatoria |
| Node.js 20+ (22 recomendado) | Frontend | Solo equipo Frontend |
| Podman (o Docker) + `podman compose` | Imágenes y entorno local completo | Para `make build` / `make up` |

## Backend (cada carpeta de `services/<x>`)

### Excepción: Problems y Knowledge

Los cambios de entorno de [Problems (PR #231)](https://github.com/help-chair/help-chair/pull/231)
y [Knowledge (PR #229)](https://github.com/help-chair/help-chair/pull/229) están
pendientes de aprobación e integración. Esta excepción se aplica con esos cambios;
no modifica el flujo de los demás servicios.

En ambos, `make setup` solo instala dependencias: no crea, copia ni carga `.env`.
El servicio consume el entorno real del proceso y exige PostgreSQL también en
local y pruebas, sin fallback SQLite. `SECRET_KEY`, `DATABASE_URL` y `ALLOWED_HOSTS`
son obligatorias; `SECRET_KEY` lo sigue siendo con DEBUG o pytest. Una variable
obligatoria ausente o vacía, o una URL de BD inválida, impide arrancar con un error
que identifica el nombre, sin revelar el valor. `.env.example` es solo un
inventario de nombres con asignaciones vacías y comentarios, no una fuente de
configuración para ejecutar.

Suministrar los valores privadamente desde el entorno o un gestor de secretos;
nunca incluirlos en Git, chat, argumentos, logs o imágenes. Consultar los README
de [Problems](../services/problems/README.md) y
[Knowledge](../services/knowledge/README.md) para su Compose propio y las
instrucciones del proveedor seguro. En Linux/WSL, `--env-file /dev/null` evita la
autocarga de `.env` por Compose. El `make up` global no acredita la adaptación de
estas variables para ambos servicios.

### Flujo genérico

```bash
cd services/<x>
make setup     # crea .env y el entorno virtual, salvo la excepción anterior (uv o venv + pip)
make test      # pytest con cobertura
make lint      # ruff
make run       # servidor en el puerto del servicio (ver tabla)
make help      # todos los comandos
```
`make` detecta solo si tienes `uv`. Sin uv usa `python3 -m venv .venv` + `requirements-dev.txt`.

### Si no puedes usar uv
`make setup` ya lo resuelve. Manual: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`.
En Windows usa WSL2 o Git Bash.

### Agregar o actualizar una dependencia (requiere uv)
```bash
uv add <paquete>            # o: uv add --group dev <paquete>
make lock                   # regenera uv.lock, requirements.txt y requirements-dev.txt
```
**Haz commit de los tres archivos juntos** (`pyproject.toml`, `uv.lock`, `requirements*.txt`).
El Dockerfile construye con `requirements.txt`; por eso no puede quedar desactualizado.
Si no tienes uv, pide a un compañero que corra `make lock` en tu rama.

## Puertos
| Servicio | App | BD local |
|---|---|---|
| events | 8001 | 5441 |
| access | 8002 | 5442 |
| requests | 8003 | 5443 |
| incidents | 8004 | 5444 |
| problems | 8005 | 5445 |
| knowledge | 8006 | 5446 |
| frontend (contenedor) / dev | 8080 / 5173 | — |

## Entorno completo (todos los servicios + BD + broker + Mailpit)
```bash
make up        # desde la raíz; usa podman compose o docker compose
make ps
make logs S=events
make down
```
Mailpit (correo de pruebas): http://localhost:8025

## Frontend
```bash
cd frontend
make setup && make test && make run   # http://localhost:5173
```

## Pre-commit (recomendado)
```bash
uv tool install pre-commit   # o: pipx install pre-commit / pip install --user pre-commit
make hooks                   # desde la raíz
```

## Contrato de OpenAPI
`make openapi` (dentro del servicio) exporta y valida `contracts/<servicio>/openapi.yaml`.
