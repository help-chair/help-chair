#!/usr/bin/env bash
# Genera ./kubeconfig-<equipo>.yaml de SOLO LECTURA con un token que caduca.
#
#   KUBECONFIG=kubeconfig-admin.yaml ./31-make-kubeconfig.sh events
#
# Variables: KUBE_SERVER  URL de la API que verá el equipo (por defecto la del kubeconfig actual;
#                         con el túnel IAP del runbook: https://127.0.0.1:6443)
#            DURATION     vigencia del token (720h = 30 días). Para renovar, vuelve a ejecutar el script.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
TEAM="${1:?Uso: $0 <equipo>   (events, access, requests, incidents, problems-kb, frontend)}"
NS="${ACCESS_NS:-hc-access}"
DURATION="${DURATION:-720h}"
need "${KUBECTL}"

SERVER="${KUBE_SERVER:-$("${KUBECTL}" config view --minify -o jsonpath='{.clusters[0].cluster.server}')}"
CA="$("${KUBECTL}" config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')"
TOKEN="$("${KUBECTL}" -n "${NS}" create token "team-${TEAM}" --duration="${DURATION}")"
OUT="kubeconfig-${TEAM}.yaml"

umask 077
cat > "${OUT}" <<YAML
apiVersion: v1
kind: Config
clusters:
  - name: hc-testing
    cluster:
      server: ${SERVER}
      certificate-authority-data: ${CA}
users:
  - name: team-${TEAM}
    user:
      token: ${TOKEN}
contexts:
  - name: hc-testing-${TEAM}
    context:
      cluster: hc-testing
      user: team-${TEAM}
current-context: hc-testing-${TEAM}
YAML
chmod 600 "${OUT}"
log "Creado ${OUT} (vigencia ${DURATION})"
echo "Compruébalo (debe decir 'no' a borrar y 'yes' a ver):"
echo "  kubectl --kubeconfig ${OUT} auth can-i delete pods -A"
echo "  kubectl --kubeconfig ${OUT} auth can-i get pods -A"
echo "Entrégalo por un canal privado: es una credencial. Está ignorado por git (kubeconfig-*.yaml)."
