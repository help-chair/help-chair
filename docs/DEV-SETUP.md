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
```bash
cd services/<x>
make setup     # crea .env y el entorno virtual (con uv o, si no hay uv, con venv + pip)
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
