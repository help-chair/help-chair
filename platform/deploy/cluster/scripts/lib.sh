#!/usr/bin/env bash
# Funciones comunes de los scripts del clúster. Se carga con: source "$(dirname "$0")/lib.sh"
# DRY_RUN=1 imprime los comandos en lugar de ejecutarlos (sirve para ensayar sin gcloud ni kubectl).

DRY_RUN="${DRY_RUN:-0}"
KUBECTL="${KUBECTL:-kubectl}"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    "$@"
  fi
}

need() {
  [[ "$DRY_RUN" == "1" ]] && return 0
  command -v "$1" >/dev/null 2>&1 || die "falta '$1' en el PATH"
}

# Valores por defecto de la VM de testing (se pueden cambiar con variables de entorno)
GCP_ZONE="${GCP_ZONE:-us-central1-a}"
# shellcheck disable=SC2034  # la usan los scripts que cargan este archivo
GCP_REGION="${GCP_ZONE%-*}"
VM_NAME="${VM_NAME:-hc-testing}"
