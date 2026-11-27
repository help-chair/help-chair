#!/usr/bin/env python3
"""Genera los manifiestos del plan B (podman kube play) a partir de una sola tabla.

Uso (desde cualquier carpeta):  python3 platform/deploy/local/kube/generate.py
Escribe un .yaml por servicio en esta misma carpeta. No necesita dependencias externas.

  --check   no escribe nada: sale con código 1 si algún manifiesto no coincide con lo que se generaría
            (alguien editó un .yaml a mano o cambió las tablas sin regenerar). Lo usa el CI.
Si cambias puertos, límites o imágenes, edita las tablas de abajo y vuelve a generar.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# nombre, puerto de la app, puerto de la BD en el host, imagen de la BD, memoria de la BD
SERVICES = [
    ("events", 8001, 5441, "docker.io/timescale/timescaledb:latest-pg16", "512Mi"),
    ("access", 8002, 5442, "docker.io/library/postgres:16-alpine", "256Mi"),
    ("requests", 8003, 5443, "docker.io/library/postgres:16-alpine", "256Mi"),
    ("incidents", 8004, 5444, "docker.io/library/postgres:16-alpine", "256Mi"),
    ("problems", 8005, 5445, "docker.io/library/postgres:16-alpine", "256Mi"),
    ("knowledge", 8006, 5446, "docker.io/library/postgres:16-alpine", "256Mi"),
]

WAIT_AND_RUN = (
    "until python -c \"import socket; socket.create_connection(('127.0.0.1', 5432), 2)\"; "
    "do echo 'esperando a la base de datos...'; sleep 2; done; "
    "python manage.py migrate --noinput && "
    "exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT "
    "--workers $WEB_CONCURRENCY --graceful-timeout 30"
)
PROBE = (
    "import os,urllib.request; "
    "urllib.request.urlopen('http://127.0.0.1:%s/health/{kind}' % os.environ['PORT'], timeout=3)"
)

HEADER = """# GENERADO por generate.py (plan B: podman kube play). No lo edites a mano.
# Cada pod trae la app y su base de datos; dentro del pod se ven por 127.0.0.1.
"""


def service_manifest(name, port, db_port, db_image, db_mem):
    env = {
        "SERVICE_NAME": name,
        "PORT": str(port),
        "DEBUG": "true",
        "SECRET_KEY": "solo-desarrollo-local",
        "ALLOWED_HOSTS": "*",
        "LOG_LEVEL": "INFO",
        "WEB_CONCURRENCY": "2",
        "DATABASE_URL": f"postgresql://{name}:{name}@127.0.0.1:5432/{name}",
    }
    if name == "access":
        env["EMPRESA_ID"] = "empresa-demo"
    env_yaml = "\n".join(
        f'        - {{name: {k}, value: "{v}"}}' for k, v in env.items()
    )
    return f"""{HEADER}apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {name}-data
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: {name}
  labels:
    app: {name}
spec:
  restartPolicy: Always
  containers:
    - name: app
      image: ghcr.io/help-chair/hc-{name}:dev
      imagePullPolicy: Never   # se construye con make kube-build
      command: ["sh", "-c", {json.dumps(WAIT_AND_RUN)}]
      env:
{env_yaml}
      ports:
        - containerPort: {port}
          hostPort: {port}
          hostIP: 127.0.0.1
      resources:
        limits:
          cpu: 500m
          memory: 256Mi
      livenessProbe:
        exec:
          command: ["python", "-c", {json.dumps(PROBE.format(kind="live"))}]
        initialDelaySeconds: 30
        periodSeconds: 15
        timeoutSeconds: 5
      readinessProbe:
        exec:
          command: ["python", "-c", {json.dumps(PROBE.format(kind="ready"))}]
        initialDelaySeconds: 20
        periodSeconds: 10
        timeoutSeconds: 5
    - name: db
      image: {db_image}
      args: ["postgres", "-c", "shared_buffers=64MB", "-c", "max_connections=50"]
      env:
        - {{name: POSTGRES_USER, value: "{name}"}}
        - {{name: POSTGRES_PASSWORD, value: "{name}"}}
        - {{name: POSTGRES_DB, value: "{name}"}}
      ports:
        - containerPort: 5432
          hostPort: {db_port}
          hostIP: 127.0.0.1
      volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      resources:
        limits:
          cpu: 500m
          memory: {db_mem}
      readinessProbe:
        exec:
          command: ["pg_isready", "-U", "{name}", "-d", "{name}"]
        periodSeconds: 5
        timeoutSeconds: 3
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: {name}-data
"""


def simple_pod(name, image, args, ports, mem, cpu="250m", probe=None, env=None):
    ports_yaml = "\n".join(
        f"        - containerPort: {c}\n          hostPort: {h}\n          hostIP: 127.0.0.1"
        for c, h in ports
    )
    args_yaml = f"\n      args: {args}" if args else ""
    env_yaml = ""
    if env:
        env_yaml = "\n      env:\n" + "\n".join(
            f'        - {{name: {k}, value: "{v}"}}' for k, v in env.items()
        )
    probe_yaml = (
        f"\n      readinessProbe:\n        exec:\n          command: {probe}\n        periodSeconds: 10"
        if probe
        else ""
    )
    return f"""{HEADER}apiVersion: v1
kind: Pod
metadata:
  name: {name}
  labels:
    app: {name}
spec:
  restartPolicy: Always
  containers:
    - name: {name}
      image: {image}{args_yaml}{env_yaml}
      ports:
{ports_yaml}
      resources:
        limits:
          cpu: {cpu}
          memory: {mem}{probe_yaml}
"""


def gateway_db_manifest():
    return f"""{HEADER}apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gateway-data
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: gateway-db
  labels:
    app: gateway-db
spec:
  restartPolicy: Always
  containers:
    - name: db
      image: docker.io/library/postgres:16-alpine
      args: ["postgres", "-c", "shared_buffers=64MB", "-c", "max_connections=50"]
      env:
        - {{name: POSTGRES_USER, value: "gateway"}}
        - {{name: POSTGRES_PASSWORD, value: "gateway"}}
        - {{name: POSTGRES_DB, value: "gateway"}}
      ports:
        - containerPort: 5432
          hostPort: 5447
          hostIP: 127.0.0.1
      volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      resources:
        limits:
          cpu: 500m
          memory: 256Mi
      readinessProbe:
        exec:
          command: ["pg_isready", "-U", "gateway", "-d", "gateway"]
        periodSeconds: 5
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: gateway-data
"""


def render_all():
    """Devuelve {nombre_de_archivo: contenido} de todos los manifiestos."""
    files = {f"{spec[0]}.yaml": service_manifest(*spec) for spec in SERVICES}
    files["gateway-db.yaml"] = gateway_db_manifest()
    files["broker.yaml"] = simple_pod(
        "broker",
        "docker.io/library/nats:2-alpine",
        '["-js", "-m", "8222"]',
        [(4222, 4222), (8222, 8222)],
        "128Mi",
        probe='["wget", "--spider", "-q", "http://127.0.0.1:8222/healthz"]',
    )
    files["mailpit.yaml"] = simple_pod(
        "mailpit",
        "docker.io/axllent/mailpit:latest",
        None,
        [(8025, 8025), (1025, 1025)],
        "64Mi",
    )
    files["frontend.yaml"] = simple_pod(
        "frontend",
        "ghcr.io/help-chair/hc-frontend:dev",
        None,
        [(8080, 8080)],
        "64Mi",
        env={"BASE_DOMAIN": "localhost"},
        probe='["wget", "--spider", "-q", "http://127.0.0.1:8080/health/live"]',
    ).replace(
        "      image: ghcr.io/help-chair/hc-frontend:dev",
        "      image: ghcr.io/help-chair/hc-frontend:dev\n      imagePullPolicy: Never",
    )
    return files


def main():
    files = render_all()
    if "--check" in sys.argv[1:]:
        bad = [
            n
            for n, c in files.items()
            if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != c
        ]
        extra = [p.name for p in HERE.glob("*.yaml") if p.name not in files]
        if bad or extra:
            print(
                "Manifiestos desactualizados o editados a mano:", ", ".join(bad + extra)
            )
            print("Regenera con: python3 platform/deploy/local/kube/generate.py")
            sys.exit(1)
        print(f"OK: {len(files)} manifiestos coinciden con generate.py")
        return
    for name, content in files.items():
        (HERE / name).write_text(content, encoding="utf-8")
    print("manifiestos escritos en", HERE)


if __name__ == "__main__":
    main()
