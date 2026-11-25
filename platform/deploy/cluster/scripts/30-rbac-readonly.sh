#!/usr/bin/env bash
# Crea una cuenta de solo lectura por equipo (ServiceAccount + rol "view" de Kubernetes).
# "view" permite ver casi todo y leer logs, pero NO leer Secrets ni modificar, ejecutar o reenviar puertos.
#
#   KUBECONFIG=kubeconfig-admin.yaml ./30-rbac-readonly.sh
#   DRY_RUN=1 ./30-rbac-readonly.sh        # solo imprime el manifiesto
#
# TEAMS: equipos con acceso de lectura. Plataforma NO está aquí: usa el kubeconfig de administrador.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
TEAMS="${TEAMS:-events access requests incidents problems-kb frontend}"
NS="${ACCESS_NS:-hc-access}"

manifest() {
  cat <<YAML
apiVersion: v1
kind: Namespace
metadata:
  name: ${NS}
YAML
  for t in ${TEAMS}; do
    cat <<YAML
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: team-${t}
  namespace: ${NS}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: team-${t}-view
subjects:
  - kind: ServiceAccount
    name: team-${t}
    namespace: ${NS}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
YAML
  done
}

if [[ "$DRY_RUN" == "1" ]]; then
  manifest
  exit 0
fi
need "${KUBECTL}"
log "Aplicando cuentas de solo lectura: ${TEAMS}"
manifest | "${KUBECTL}" apply -f -
log "Siguiente: ./31-make-kubeconfig.sh <equipo> para cada equipo"
