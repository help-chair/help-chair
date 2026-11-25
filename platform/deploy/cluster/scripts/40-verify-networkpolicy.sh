#!/usr/bin/env bash
# Comprueba que el CNI del clúster APLICA las NetworkPolicy (requisito de la fase 4: aislar empresas).
#
#   KUBECONFIG=kubeconfig-admin.yaml ./40-verify-networkpolicy.sh
#
# Prueba: un servidor en el namespace A. Sin política, el namespace B lo alcanza. Con una política que
# solo admite pods de A, B queda bloqueado y A sigue funcionando. Termina con código 1 si no se aplica.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
need "${KUBECTL}"
A="np-test-a"; B="np-test-b"
IMG_WEB="docker.io/library/nginx:1.27-alpine"
IMG_CLI="docker.io/library/busybox:1.36"
URL="http://web.${A}.svc.cluster.local"

cleanup() { "${KUBECTL}" delete ns "${A}" "${B}" --ignore-not-found --wait=false >/dev/null 2>&1 || true; }
trap cleanup EXIT

probe() { # <namespace> -> 0 si llega al servidor
  "${KUBECTL}" -n "$1" run "probe-${RANDOM}" --image="${IMG_CLI}" --rm -i --restart=Never --quiet \
    --command -- wget -q -O /dev/null -T 4 "${URL}" >/dev/null 2>&1
}

log "Preparando namespaces y servidor"
"${KUBECTL}" create ns "${A}" >/dev/null; "${KUBECTL}" create ns "${B}" >/dev/null
"${KUBECTL}" -n "${A}" create deployment web --image="${IMG_WEB}" >/dev/null
"${KUBECTL}" -n "${A}" expose deployment web --port 80 >/dev/null
"${KUBECTL}" -n "${A}" rollout status deployment/web --timeout=120s >/dev/null

fail=0
check() { # <descripción> <esperado: ok|blocked> <namespace>
  local got="blocked"; probe "$3" && got="ok"
  if [[ "$got" == "$2" ]]; then echo "  PASS  $1"; else echo "  FAIL  $1 (esperado: $2, obtenido: $got)"; fail=1; fi
}

log "Sin política"
check "desde ${B} se alcanza el servidor (línea base)" ok "${B}"

log "Aplicando política: solo entran pods del propio namespace"
"${KUBECTL}" apply -f - >/dev/null <<YAML
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: solo-mismo-namespace
  namespace: ${A}
spec:
  podSelector: {}
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector: {}
YAML
sleep 5
check "desde ${B} el servidor queda BLOQUEADO" blocked "${B}"
check "desde ${A} el servidor sigue accesible" ok "${A}"

if [[ "$fail" == "0" ]]; then
  log "OK: el CNI aplica NetworkPolicy."
else
  die "el CNI NO está aplicando NetworkPolicy. En k3s revisa que no se haya instalado con --disable-network-policy."
fi
