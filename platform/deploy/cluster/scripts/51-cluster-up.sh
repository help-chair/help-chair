#!/usr/bin/env bash
# Enciende la VM de testing y espera a que el nodo vuelva a estar Ready.
#   KUBECONFIG=kubeconfig-admin.yaml ./51-cluster-up.sh      o      make testing-up
# Sin KUBECONFIG solo enciende la VM. Si usas túnel SSH, ábrelo antes de que termine la espera.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
need gcloud
log "Encendiendo ${VM_NAME}"
run gcloud compute instances start "${VM_NAME}" --zone "${GCP_ZONE}"

if [[ -z "${KUBECONFIG:-}" ]]; then
  echo "KUBECONFIG no está definido: no se espera al nodo. Comprueba con: kubectl get nodes"
  exit 0
fi
[[ "$DRY_RUN" == "1" ]] && exit 0
need "${KUBECTL}"
log "Esperando al nodo (hasta 5 minutos)"
for _ in $(seq 1 60); do
  if "${KUBECTL}" get nodes 2>/dev/null | grep -q " Ready"; then
    "${KUBECTL}" get nodes
    log "Pods que aún no están Running (los de los stacks tardan un poco más):"
    "${KUBECTL}" get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded || true
    exit 0
  fi
  sleep 5
done
die "el nodo no volvió a Ready en 5 minutos: revisa con 'gcloud compute ssh ${VM_NAME}' y 'sudo journalctl -u k3s'"
