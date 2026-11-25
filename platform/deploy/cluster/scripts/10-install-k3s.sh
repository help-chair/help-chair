#!/usr/bin/env bash
# Se ejecuta DENTRO de la VM. Instala k3s (un solo nodo) con secretos cifrados en disco.
#
#   TLS_SAN=<IP pública> ./10-install-k3s.sh
#
# Variables: TLS_SAN (obligatoria: IP o nombre con el que se llegará a la API)
#            INGRESS_CONTROLLER  traefik (por defecto, viene con k3s) | nginx (ver el runbook: está retirado)
#            K3S_VERSION  fija la versión (recomendado), p. ej. v1.34.1+k3s1 (consulta la última estable)
# k3s trae también CoreDNS, ServiceLB, local-path (PVC), metrics-server y el controlador de
# NetworkPolicy (kube-router): NO se desactivan.
set -euo pipefail

: "${TLS_SAN:?Define TLS_SAN con la IP pública de la VM}"
INGRESS_CONTROLLER="${INGRESS_CONTROLLER:-traefik}"

args="server --tls-san ${TLS_SAN} --secrets-encryption --write-kubeconfig-mode 600"
case "${INGRESS_CONTROLLER}" in
  traefik) ;;
  nginx)   args="${args} --disable traefik" ;;
  *)       echo "INGRESS_CONTROLLER debe ser traefik o nginx" >&2; exit 1 ;;
esac

echo "==> Instalando k3s (${args})"
curl -sfL https://get.k3s.io | \
  INSTALL_K3S_EXEC="${args}" ${K3S_VERSION:+INSTALL_K3S_VERSION="${K3S_VERSION}"} sh -

echo "==> Esperando a que el nodo esté Ready"
sudo k3s kubectl wait --for=condition=Ready node --all --timeout=180s
sudo k3s kubectl get nodes -o wide
echo "Listo. Siguiente: 11-fetch-admin-kubeconfig.sh desde tu máquina."
