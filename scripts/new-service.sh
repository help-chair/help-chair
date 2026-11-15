#!/usr/bin/env bash
# Crea (o completa) un servicio Django a partir de platform/templates/django-service.
# Uso: ./scripts/new-service.sh <nombre> <puerto> [puerto-bd-local]
# Ej.: ./scripts/new-service.sh events 8001 5441
# No sobrescribe archivos existentes (README.md del equipo, código ya escrito).
set -euo pipefail

NAME="${1:?Uso: $0 <nombre> <puerto> [puerto-bd]}"
PORT="${2:?Falta el puerto}"
DBPORT="${3:-$((PORT - 8001 + 5441))}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/platform/templates/django-service"
DEST="$ROOT/services/$NAME"

mkdir -p "$DEST"
cd "$SRC"
find . -type f ! -path '*/__pycache__/*' | while read -r f; do
  target="$DEST/$f"
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" ]]; then
    echo "  = conserva $NAME/$f"
  else
    sed -e "s/__SERVICE__/$NAME/g" -e "s/__PORT__/$PORT/g" -e "s/__DBPORT__/$DBPORT/g" "$f" > "$target"
    [[ "$f" == "./manage.py" ]] && chmod +x "$target"
    echo "  + crea     $NAME/$f"
  fi
done

if command -v uv >/dev/null 2>&1; then
  echo "==> uv encontrado: generando uv.lock y requirements*.txt"
  (cd "$DEST" && make lock)
else
  echo "⚠ uv no está instalado: no se pudo generar uv.lock/requirements.txt."
  echo "  Instala uv (https://docs.astral.sh/uv/) y ejecuta 'make lock' dentro de services/$NAME"
fi
echo "✔ services/$NAME listo."
