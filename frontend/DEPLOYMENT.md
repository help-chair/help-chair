# Guía de Despliegue y Operaciones · Help Chair Frontend

[English version below ↓](#english-version)

Esta guía documenta cómo desplegar, configurar y verificar en producción el contenedor de **Frontend** de Help Chair: el **sitio público** (`help-chair.com`) y el **Service Desk** (`empresaN.help-chair.com`) salen de la **misma imagen**.

---

## 🇪🇸 Español

### 1. Información del Contenedor

- **Imagen oficial:** `ghcr.io/help-chair/hc-frontend:<versión>`
- **Usuario de ejecución:** No-root (`nginx` - UID 101).
- **Puerto expuesto:** `8080` (HTTP).
- **Consumo de recursos estimado:** ~15MB RAM, < 0.1 CPU en reposo.

### 2. Configuración (una sola imagen para todo)

La imagen **no incrusta ninguna URL ni dominio** al construirse. Al arrancar, el script `docker/40-hc-config.sh` genera `/config.json` a partir de una variable:

| Variable | Descripción | Por defecto |
|---|---|---|
| `BASE_DOMAIN` | Dominio base del producto (p. ej. `help-chair.com`). El dominio exacto y `www.` son el sitio público; `<empresa>.<BASE_DOMAIN>` es el Service Desk de esa empresa | `localhost` |

- Solo se aceptan letras, números, puntos y guiones; cualquier otro valor detiene el arranque.
- `/config.json` se sirve con `Cache-Control: no-store`.
- Las variables `VITE_*` **no se usan en producción**: Vite las incrusta al compilar y la imagen ya viene compilada.

### 3. Enrutamiento de `/api` (importante)

El contenedor solo sirve los archivos estáticos. **No atiende `/api/*`**: el cliente llama a rutas relativas y las resuelve el gateway/ingress según el `Host`:

| Host | `/api/...` va a |
|---|---|
| `help-chair.com` | Registro de empresas del gateway (`/api/public/v1/*`) |
| `empresaN.help-chair.com` | El stack de la empresa (`/api/<servicio>/...`) |

Por eso este contenedor siempre debe ir detrás del ingress/gateway de Plataforma.

### 4. Endpoints de Salud (Health Checks)

- **Liveness:** `GET http://<host>:8080/health/live`  
  _Respuesta:_ `{"status":"ok"}` (Código HTTP 200).
- **Readiness:** `GET http://<host>:8080/health/ready`  
  _Respuesta:_ `{"status":"ok"}` (Código HTTP 200).

### 5. Prueba rápida con un solo contenedor

```bash
podman run --rm -p 8080:8080 -e BASE_DOMAIN=help-chair.com ghcr.io/help-chair/hc-frontend:dev
curl localhost:8080/config.json        # {"BASE_DOMAIN":"help-chair.com"}
curl localhost:8080/health/live
```

Sin gateway las llamadas a `/api` devuelven 404 (es lo esperado).

### 6. Despliegue en Kubernetes (Stack por Empresa)

El mismo Deployment sirve al sitio público y a cada empresa; solo cambia el Ingress. Manifiesto típico:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hc-frontend
  namespace: tenant-empresa1
  labels:
    app.kubernetes.io/name: hc-frontend
    app.kubernetes.io/part-of: help-chair
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: hc-frontend
  template:
    metadata:
      labels:
        app.kubernetes.io/name: hc-frontend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101
      containers:
        - name: frontend
          image: ghcr.io/help-chair/hc-frontend:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          env:
            - name: BASE_DOMAIN
              value: help-chair.com
          resources:
            requests:
              cpu: 50m
              memory: 32Mi
            limits:
              cpu: 200m
              memory: 64Mi
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: hc-frontend
  namespace: tenant-empresa1
spec:
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app.kubernetes.io/name: hc-frontend
```

> Plataforma define el Ingress: `help-chair.com` → frontend + `/api/public/*` al gateway; `*.help-chair.com` → frontend + `/api/*` al stack de la empresa. Ver `docs/REGISTRO-EMPRESA.md`.

---

<a name="english-version"></a>

## 🇬🇧 English

### 1. Container Information

- **Official image:** `ghcr.io/help-chair/hc-frontend:<version>`
- **Execution user:** Non-root (`nginx` - UID 101).
- **Exposed port:** `8080` (HTTP).
- **Estimated resources:** ~15MB RAM, < 0.1 CPU at rest.

### 2. Configuration (one image for everything)

The image **bakes in no URL or domain** at build time. On start, `docker/40-hc-config.sh` writes `/config.json` from one variable:

| Variable | Description | Default |
|---|---|---|
| `BASE_DOMAIN` | Product base domain (e.g. `help-chair.com`). The exact domain and `www.` are the public site; `<company>.<BASE_DOMAIN>` is that company's Service Desk | `localhost` |

`VITE_*` variables are **not used in production** (Vite bakes them in at build time).

### 3. `/api` routing

The container only serves static files. `/api/*` is resolved by the gateway/ingress by `Host` (public sign-up API on `help-chair.com`; the company stack on `companyN.help-chair.com`). It must always run behind Platform's ingress/gateway.

### 4. Health Checks

- **Liveness:** `GET http://<host>:8080/health/live` → `{"status":"ok"}` (HTTP 200).
- **Readiness:** `GET http://<host>:8080/health/ready` → `{"status":"ok"}` (HTTP 200).

### 5. Quickstart

```bash
podman run --rm -p 8080:8080 -e BASE_DOMAIN=help-chair.com ghcr.io/help-chair/hc-frontend:dev
curl localhost:8080/config.json
```

### 6. Kubernetes

Use the Deployment above (Spanish section); set `BASE_DOMAIN` as an environment variable. The same Deployment serves the public site and every company; only the Ingress differs.
