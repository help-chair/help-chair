#!/usr/bin/env bash
# helm lint + helm template de cada ambiente (y kubeconform si está instalado).
# REQUIRE_KUBECONFORM=true (lo pone Jenkins) hace fallar el script si falta kubeconform.
# Uso:  ./platform/deploy/helm/check.sh        o        make helm-check
set -euo pipefail

CHART="$(cd "$(dirname "$0")/stack" && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

command -v helm >/dev/null || { echo "ERROR: helm no está instalado" >&2; exit 1; }

# 1) cada services/<x>.yaml debe llamarse igual que su "name" (el chart también lo comprueba)
for f in "$CHART"/services/*.yaml; do
  n="$(basename "$f" .yaml)"
  grep -Eq "^name: ${n}\s*(#.*)?$" "$f" || { echo "ERROR: $f debe declarar 'name: ${n}'" >&2; exit 1; }
done

# 2) lint y template por ambiente
for env in dev testing production; do
  echo "== ${env}"
  helm lint "$CHART" -f "$CHART/values-${env}.yaml" --set global.imageTag=ci
  helm template hc-stack "$CHART" -n "empresa-ci" -f "$CHART/values-${env}.yaml" \
    --set global.imageTag=ci > "$OUT/${env}.yaml"
  echo "   $(grep -c '^kind:' "$OUT/${env}.yaml") recursos renderizados"
done

# 3) esquema de Kubernetes (opcional)
if command -v kubeconform >/dev/null; then
  kubeconform -strict -summary -kubernetes-version "${K8S_VERSION:-1.35.0}" "$OUT"/*.yaml
elif [[ "${REQUIRE_KUBECONFORM:-}" == "true" ]]; then
  echo "ERROR: kubeconform no está instalado y REQUIRE_KUBECONFORM=true" >&2
  exit 1
else
  echo "(kubeconform no está instalado: se omite la validación contra el esquema de Kubernetes)"
fi
echo "OK: el chart es válido en dev, testing y production."
