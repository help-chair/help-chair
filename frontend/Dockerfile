# Imagen: ghcr.io/help-chair/hc-frontend
# UNA sola imagen para todos los ambientes y empresas: no se incrusta ninguna URL al construir.
# La configuración de tiempo de ejecución (BASE_DOMAIN) se genera al arrancar en /config.json
# (ver docker/40-hc-config.sh) y la API se consume con rutas relativas (/api/...).
#   podman run -p 8080:8080 -e BASE_DOMAIN=help-chair.com ghcr.io/help-chair/hc-frontend:dev
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# nginx-unprivileged: corre como usuario no root y escucha en un puerto > 1024
FROM nginxinc/nginx-unprivileged:1.27-alpine
USER root
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/40-hc-config.sh /docker-entrypoint.d/40-hc-config.sh
RUN chmod 755 /docker-entrypoint.d/40-hc-config.sh \
 && chown -R nginx:nginx /usr/share/nginx/html
USER nginx
ENV BASE_DOMAIN=localhost
EXPOSE 8080
