# Guía de Despliegue y Operaciones · Help Chair Frontend (Service Desk)

[English version below ↓](#english-version)

Esta guía documenta cómo desplegar, configurar y verificar en producción el contenedor de **Frontend (Service Desk)** de Help Chair.

---

## 🇪🇸 Español

### 1. Información del Contenedor

- **Imagen oficial:** `ghcr.io/help-chair/hc-frontend:<versión>`
- **Usuario de ejecución:** No-root (`nginx` - UID 101).
- **Puerto expuesto:** `8080` (HTTP).
- **Consumo de recursos estimado:** ~15MB RAM, < 0.1 CPU en reposo.

### 2. Endpoints de Salud (Health Checks)

Cumpliendo con la arquitectura de Help Chair, el contenedor expone:

- **Liveness:** `GET http://<host>:8080/health/live`  
  _Respuesta:_ `{"status":"UP","check":"liveness"}` (Código HTTP 200).
- **Readiness:** `GET http://<host>:8080/health/ready`  
  _Respuesta:_ `{"status":"UP","check":"readiness"}` (Código HTTP 200).

### 3. Despliegue con Docker Compose (Producción / Staging)

Para desplegar la aplicación en un servidor o máquina virtual para una empresa cliente:

1. Crea un archivo `docker-compose.yml`:

```yaml
services:
  service-desk:
    image: ghcr.io/help-chair/hc-frontend:1.0.0
    container_name: helpchair-frontend
    restart: unless-stopped
    ports:
      - '80:8080'
    healthcheck:
      test: ['CMD', 'wget', '-qO-', 'http://localhost:8080/health/live']
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 5s
    environment:
      - VITE_API_GATEWAY_URL=https://gateway.helpchair.example
      - VITE_USE_MOCKS=false
```

2. Inicia el contenedor:

```bash
docker compose up -d
```

### 4. Despliegue en Kubernetes (Stack por Empresa)

Dentro del namespace asignado a la empresa (`tenant-<nombre>`), el manifiesto típico es:

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

---

<a name="english-version"></a>

## 🇬🇧 English

### 1. Container Information

- **Official image:** `ghcr.io/help-chair/hc-frontend:<version>`
- **Execution user:** Non-root (`nginx` - UID 101).
- **Exposed port:** `8080` (HTTP).
- **Estimated resources:** ~15MB RAM, < 0.1 CPU at rest.

### 2. Health Checks

- **Liveness:** `GET http://<host>:8080/health/live` (HTTP 200).
- **Readiness:** `GET http://<host>:8080/health/ready` (HTTP 200).

### 3. Production Quickstart

```bash
docker run -d --name hc-frontend -p 80:8080 ghcr.io/help-chair/hc-frontend:1.0.0
```

Verify status at `http://localhost/health/live`.
