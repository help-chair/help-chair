#!/usr/bin/env bash
# Verifica (o instala) el ingress y metrics-server. Se ejecuta desde tu máquina con KUBECONFIG de admin.
#
#   KUBECONFIG=kubeconfig-admin.yaml ./20-install-addons.sh
#
# INGRESS_CONTROLLER=traefik (por defecto): ya viene con k3s, solo se verifica.
# INGRESS_CONTROLLER=nginx: instala ingress-nginx con Helm. El proyecto está RETIRADO (marzo de 2026):
#   no recibe parches de seguridad. Hay que aceptarlo de forma explícita con ACCEPT_RETIRED_INGRESS_NGINX=yes.
#   El k3s debe haberse instalado con INGRESS_CONTROLLER=nginx (desactiva Traefik).
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
INGRESS_CONTROLLER="${INGRESS_CONTROLLER:-traefik}"
need "${KUBECTL}"

case "${INGRESS_CONTROLLER}" in
  traefik)
    log "Ingress: Traefik (incluido en k3s)"
    run "${KUBECTL}" -n kube-system rollout status deploy/traefik --timeout=180s
    run "${KUBECTL}" get ingressclass
    ;;
  nginx)
    [[ "${ACCEPT_RETIRED_INGRESS_NGINX:-}" == "yes" ]] || \
      die "ingress-nginx está retirado. Si aun así lo quieres: ACCEPT_RETIRED_INGRESS_NGINX=yes"
    need helm
    log "Ingress: ingress-nginx (RETIRADO: sin parches de seguridad)"
    run helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    run helm repo update
    run helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
      --namespace ingress-nginx --create-namespace \
      --set controller.service.type=LoadBalancer \
      --set controller.ingressClassResource.default=true
    run "${KUBECTL}" -n ingress-nginx rollout status deploy/ingress-nginx-controller --timeout=240s
    ;;
  *) die "INGRESS_CONTROLLER debe ser traefik o nginx" ;;
esac

log "metrics-server (incluido en k3s)"
run "${KUBECTL}" -n kube-system rollout status deploy/metrics-server --timeout=180s
if [[ "$DRY_RUN" != "1" ]]; then
  for _ in $(seq 1 18); do
    if "${KUBECTL}" top nodes 2>/dev/null; then break; fi
    echo "   esperando las primeras métricas..."; sleep 10
  done
fi
log "Nodos"
run "${KUBECTL}" get nodes
