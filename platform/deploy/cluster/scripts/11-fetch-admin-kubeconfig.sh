#!/usr/bin/env bash
# Descarga el kubeconfig de ADMINISTRADOR (solo Plataforma) a ./kubeconfig-admin.yaml
#
#   SERVER_HOST=<IP pública> ./11-fetch-admin-kubeconfig.sh      # API expuesta (API_CIDR)
#   SERVER_HOST=127.0.0.1    ./11-fetch-admin-kubeconfig.sh      # con túnel SSH (ver el runbook)
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
: "${SERVER_HOST:?Define SERVER_HOST (IP pública de la VM o 127.0.0.1 si usas túnel SSH)}"
need gcloud

OUT="${OUT:-kubeconfig-admin.yaml}"
umask 077
log "Descargando el kubeconfig de ${VM_NAME}"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] gcloud compute ssh ${VM_NAME} --zone ${GCP_ZONE} --command 'sudo cat /etc/rancher/k3s/k3s.yaml' | sed ... > ${OUT}"
  exit 0
fi
gcloud compute ssh "${VM_NAME}" --zone "${GCP_ZONE}" --command 'sudo cat /etc/rancher/k3s/k3s.yaml' \
  | sed "s#https://127.0.0.1:6443#https://${SERVER_HOST}:6443#" > "${OUT}"
chmod 600 "${OUT}"
echo "Guardado en ${OUT}. Es de ADMINISTRADOR: no lo compartas ni lo subas al repositorio."
echo "Prueba:  KUBECONFIG=${OUT} kubectl get nodes"
