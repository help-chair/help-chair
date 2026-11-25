#!/usr/bin/env bash
# Apaga la VM de testing para no gastar crédito. Los datos (PVC) se conservan en el disco.
#   ./50-cluster-down.sh      o      make testing-down
# Cuesta solo el disco y la IP estática mientras está apagada.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
need gcloud
log "Apagando ${VM_NAME} (apagado ordenado: PostgreSQL recibe SIGTERM)"
run gcloud compute instances stop "${VM_NAME}" --zone "${GCP_ZONE}"
log "Apagada. Enciéndela con: make testing-up"
