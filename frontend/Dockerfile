# Imagen: ghcr.io/help-chair/hc-frontend
# La URL de la API se fija al construir (Vite incrusta VITE_* en el bundle):
#   podman build --build-arg VITE_API_BASE_URL=https://api.empresa.helpchair.example -t ghcr.io/help-chair/hc-frontend:dev .
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8001
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# nginx-unprivileged: corre como usuario no root y escucha en un puerto > 1024
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
