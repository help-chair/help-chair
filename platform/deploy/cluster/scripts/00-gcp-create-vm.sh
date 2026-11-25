#!/usr/bin/env bash
# Crea en Google Cloud la VM de testing: IP estática, reglas de firewall y la VM (Ubuntu 24.04).
#
#   PROJECT_ID=mi-proyecto ./00-gcp-create-vm.sh
#
# Variables: PROJECT_ID (obligatoria) · GCP_ZONE (us-central1-a) · VM_NAME (hc-testing)
#            MACHINE_TYPE (e2-standard-4) · DISK_GB (60)
#            ALLOW_IAP  1 (por defecto) = permite el túnel IAP de Google (35.235.240.0/20) a los puertos 22 y 6443.
#                      Es la forma recomendada de llegar a la API: cada integrante necesita solo el rol
#                      "IAP-secured Tunnel User", NO acceso a la VM (ver el runbook).
#            API_CIDR  IP pública en formato CIDR (p. ej. 201.1.2.3/32) desde la que se abre la API (6443)
#                      directamente a internet. Vacío = no se abre. Solo si no puedes usar IAP.
#            DRY_RUN=1 solo imprime los comandos.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

: "${PROJECT_ID:?Define PROJECT_ID (gcloud projects list)}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-4}"
DISK_GB="${DISK_GB:-60}"
API_CIDR="${API_CIDR:-}"
ALLOW_IAP="${ALLOW_IAP:-1}"
need gcloud

log "Proyecto ${PROJECT_ID} · zona ${GCP_ZONE} · ${MACHINE_TYPE} · disco ${DISK_GB} GB"
run gcloud config set project "${PROJECT_ID}"

log "IP estática (sin ella la IP cambia cada vez que apagas la VM)"
if [[ "$DRY_RUN" == "1" ]] || ! gcloud compute addresses describe "${VM_NAME}-ip" --region "${GCP_REGION}" >/dev/null 2>&1; then
  run gcloud compute addresses create "${VM_NAME}-ip" --region "${GCP_REGION}"
else
  echo "   ya existe ${VM_NAME}-ip"
fi

log "Firewall: HTTP y HTTPS abiertos; la API de Kubernetes solo si defines API_CIDR"
if [[ "$DRY_RUN" == "1" ]] || ! gcloud compute firewall-rules describe "${VM_NAME}-web" >/dev/null 2>&1; then
  run gcloud compute firewall-rules create "${VM_NAME}-web" \
    --allow tcp:80,tcp:443 --target-tags "${VM_NAME}" --source-ranges 0.0.0.0/0
fi
if [[ "$ALLOW_IAP" == "1" ]]; then
  if [[ "$DRY_RUN" == "1" ]] || ! gcloud compute firewall-rules describe "${VM_NAME}-iap" >/dev/null 2>&1; then
    run gcloud compute firewall-rules create "${VM_NAME}-iap" \
      --allow tcp:22,tcp:6443 --target-tags "${VM_NAME}" --source-ranges 35.235.240.0/20
  fi
fi
if [[ -n "$API_CIDR" ]]; then
  if [[ "$DRY_RUN" == "1" ]] || ! gcloud compute firewall-rules describe "${VM_NAME}-kubeapi" >/dev/null 2>&1; then
    run gcloud compute firewall-rules create "${VM_NAME}-kubeapi" \
      --allow tcp:6443 --target-tags "${VM_NAME}" --source-ranges "${API_CIDR}"
  fi
else
  echo "   API_CIDR vacío: la API (6443) NO se abre a internet; se llega por el túnel IAP (runbook)."
fi

log "VM"
if [[ "$DRY_RUN" == "1" ]] || ! gcloud compute instances describe "${VM_NAME}" --zone "${GCP_ZONE}" >/dev/null 2>&1; then
  run gcloud compute instances create "${VM_NAME}" \
    --zone "${GCP_ZONE}" --machine-type "${MACHINE_TYPE}" \
    --image-family ubuntu-2404-lts-amd64 --image-project ubuntu-os-cloud \
    --boot-disk-size "${DISK_GB}GB" --boot-disk-type pd-balanced \
    --address "${VM_NAME}-ip" --tags "${VM_NAME}"
else
  echo "   ya existe ${VM_NAME}"
fi

if [[ "$DRY_RUN" != "1" ]]; then
  IP="$(gcloud compute addresses describe "${VM_NAME}-ip" --region "${GCP_REGION}" --format 'value(address)')"
  log "Listo. IP pública: ${IP}"
  echo "Siguiente: copia y ejecuta 10-install-k3s.sh en la VM (si SSH directo no responde, añade --tunnel-through-iap):"
  echo "  gcloud compute scp 10-install-k3s.sh ${VM_NAME}:~ --zone ${GCP_ZONE}"
  echo "  gcloud compute ssh ${VM_NAME} --zone ${GCP_ZONE} --command 'TLS_SAN=${IP} bash 10-install-k3s.sh'"
fi
