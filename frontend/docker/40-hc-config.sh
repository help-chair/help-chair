#!/bin/sh
# Genera config.json con la configuración de tiempo de ejecución al arrancar el contenedor.
# nginx ejecuta los scripts de /docker-entrypoint.d/ antes de iniciar.
set -eu

BASE_DOMAIN="${BASE_DOMAIN:-localhost}"
HTML_DIR="${HTML_DIR:-/usr/share/nginx/html}"

case "$BASE_DOMAIN" in
  ""|*[!a-zA-Z0-9.-]*)
    echo "hc-config: BASE_DOMAIN inválido: '$BASE_DOMAIN'" >&2
    exit 1
    ;;
esac

printf '{"BASE_DOMAIN":"%s"}\n' "$BASE_DOMAIN" > "$HTML_DIR/config.json"
echo "hc-config: config.json generado (BASE_DOMAIN=$BASE_DOMAIN)"
