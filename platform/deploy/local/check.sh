#!/usr/bin/env bash
# Valida el entorno local: compose.yaml, manifiestos de kube play y que estén al día.
#   ./platform/deploy/local/check.sh      o      make compose-check
# REQUIRE_KUBECONFORM=true (lo pone Jenkins) hace fallar el script si falta kubeconform.
set -euo pipefail
cd "$(dirname "$0")"

echo "== compose.yaml"
if command -v uv >/dev/null 2>&1; then
  uv run --quiet --with pyyaml python check_compose.py
else
  python3 check_compose.py
fi

echo "== manifiestos de kube play"
python3 kube/generate.py --check
if command -v kubeconform >/dev/null 2>&1; then
  kubeconform -strict -summary -kubernetes-version "${K8S_VERSION:-1.35.0}" kube/*.yaml
elif [[ "${REQUIRE_KUBECONFORM:-}" == "true" ]]; then
  echo "ERROR: kubeconform no está instalado y REQUIRE_KUBECONFORM=true" >&2
  exit 1
else
  echo "(kubeconform no está instalado: se omite la validación contra el esquema de Kubernetes)"
fi
echo "OK: entorno local válido."
