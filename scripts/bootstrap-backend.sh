#!/usr/bin/env bash
# Crea los 6 servicios backend con la plantilla. Ejecutar una sola vez (Plataforma).
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/new-service.sh events    8001 5441
./scripts/new-service.sh access    8002 5442
./scripts/new-service.sh requests  8003 5443
./scripts/new-service.sh incidents 8004 5444
./scripts/new-service.sh problems  8005 5445
./scripts/new-service.sh knowledge 8006 5446
