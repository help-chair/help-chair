#!/usr/bin/env python3
"""Comprueba que compose.yaml cumple lo acordado para el entorno local.

Uso:  uv run --with pyyaml python platform/deploy/local/check_compose.py     (o python3 con PyYAML)
Sale con código 1 y lista los problemas si algo no se cumple. Lo ejecuta `make compose-check`.
"""

import sys
from pathlib import Path

import yaml

COMPOSE = Path(__file__).resolve().parent / "compose.yaml"
REQUIRED = {
    "broker",
    "mailpit",
    "frontend",
}  # además de un servicio y una BD por cada equipo


def main() -> int:
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services = data.get("services", {})
    volumes = data.get("volumes") or {}
    errors: list[str] = []

    if not data.get("name"):
        errors.append(
            "falta `name:` (sin él, el proyecto y los volúmenes se llamarían `local`)"
        )

    for name in REQUIRED - set(services):
        errors.append(f"falta el servicio `{name}`")

    for name, svc in services.items():
        limits = (svc.get("deploy") or {}).get("resources", {}).get("limits") or {}
        for key in ("cpus", "memory"):
            if key not in limits:
                errors.append(f"{name}: falta deploy.resources.limits.{key}")
        for port in svc.get("ports", []):
            if not str(port).startswith("127.0.0.1:"):
                errors.append(
                    f"{name}: el puerto {port} debe publicarse solo en 127.0.0.1"
                )
        first, slash, _ = (svc.get("image") or "").partition("/")
        if not slash or not ("." in first or ":" in first or first == "localhost"):
            errors.append(
                f"{name}: la imagen `{svc.get('image')}` necesita el registro completo (docker.io/...)"
            )

    # una base de datos con volumen con nombre por cada servicio de la aplicación
    apps = [n for n, s in services.items() if "build" in s and n != "frontend"]
    for app in apps:
        db = services.get(f"{app}-db")
        if db is None:
            errors.append(f"{app}: falta su base de datos `{app}-db`")
            continue
        mounts = [v.split(":")[0] for v in db.get("volumes", [])]
        if not mounts:
            errors.append(f"{app}-db: sin volumen para los datos")
        for volume in mounts:
            if volume not in volumes:
                errors.append(
                    f"{app}-db: el volumen `{volume}` no está declarado en `volumes:`"
                )
        depends = services[app].get("depends_on") or {}
        condition = (
            depends.get(f"{app}-db", {}).get("condition")
            if isinstance(depends, dict)
            else None
        )
        if condition != "service_healthy":
            errors.append(
                f"{app}: debe depender de {app}-db con condition: service_healthy"
            )

    if errors:
        print("compose.yaml no cumple:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(
        f"OK: {len(services)} servicios; {len(apps)} aplicaciones, cada una con su BD y volumen con nombre; "
        "límites en todos; puertos solo en 127.0.0.1"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
