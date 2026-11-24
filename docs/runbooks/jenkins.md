# Runbook: Jenkins (CI/CD)

> Issue #85 · Dueño: Plataforma (`platform/deploy/jenkins/`) · Práctica ITIL v4: Deployment Management

Jenkins ejecuta el `Jenkinsfile` de cada servicio (`make lint test`, `make build`) cada vez que cambia una rama o un PR.
**Toda su configuración es código** y vive en `platform/deploy/jenkins/`. Lo que se cambie desde la interfaz web se pierde al reiniciar.

## 1. Qué hay y dónde vive

| Pieza | Archivo o lugar | ¿En git? |
|---|---|---|
| Versión de Jenkins, `make` y `uv` | `Dockerfile` | ✅ |
| Plugins | `plugins.txt` | ✅ |
| Usuarios, roles, credenciales, jobs y disparadores | `casc.yaml` (JCasC + Job DSL) | ✅ |
| Cómo se levanta (puerto, volumen) | Servicio `jenkins` (perfil `ci`) en `platform/deploy/local/compose.yaml` | ✅ |

| **Secretos** (contraseñas y tokens) | `platform/deploy/jenkins/.env` | ❌ **Nunca** |
| Historial de builds, workspaces y cachés | Volumen `local_jenkins-home` | ❌ (se respalda aparte, ver §6) |

Usuarios: `admin` (Plataforma) y uno por equipo: `team-events`, `team-access`, `team-requests`, `team-incidents`, `team-problems` (Problemas + KB) y `team-frontend`.

| Rol | Puede |
|---|---|
| `admin` | Todo (Administrar Jenkins) |
| Cada equipo | Ver todos los jobs; **ejecutar, cancelar y repetir solo los de su servicio** |

Jobs: uno multibranch por servicio (`events`, `access`, `requests`, `incidents`, `problems`, `knowledge`, `frontend`).
Cada uno busca `services/<servicio>/Jenkinsfile` (o `frontend/Jenkinsfile`) en todas las ramas y PR, y revisa GitHub **cada 2 minutos**.

## 2. Requisitos

- Docker (probado con Docker 29 en Windows) o Podman con `podman compose`.
- 2 GB de RAM libres y 5 GB de disco como mínimo.
- Acceso a internet (Docker Hub, ghcr.io, updates.jenkins.io y api.github.com).

## 3. Crear los tokens de GitHub (una sola vez)

En GitHub: **Settings → Developer settings → Personal access tokens**.

| Variable | Token | Permisos (mínimo privilegio) |
|---|---|---|
| `GITHUB_USER` / `GITHUB_TOKEN` | *Fine-grained*, recurso `help-chair/help-chair` | Contents: **Read**, Metadata: **Read**, Pull requests: **Read** |
| `GHCR_USER` / `GHCR_TOKEN` | *Classic* | `write:packages` (y `read:packages`) |

- Si la organización exige aprobar los tokens *fine-grained*, un owner de `help-chair` debe aprobarlo.
- Los tokens caducan: anota la fecha de expiración en el canal del equipo y renuévalos antes.
- `*_USER` es el usuario de GitHub de quien crea el token.

## 4. Instalación

Desde la raíz del repo:

```bash
cp platform/deploy/jenkins/.env.example platform/deploy/jenkins/.env
# Edita .env: una contraseña distinta por usuario (mínimo 16 caracteres) y los tokens del paso 3.
docker compose -f platform/deploy/local/compose.yaml --profile ci up -d --build jenkins
```

La primera construcción descarga los plugins y tarda de 1 a 3 minutos. Jenkins queda en **http://localhost:8090** (8090 porque el 8080 lo usa el frontend).

Las contraseñas se reparten **por mensaje privado** a cada equipo, nunca en el canal general ni en un issue.

## 5. Verificación (después de instalar o cambiar algo)

1. `http://localhost:8090` pide iniciar sesión (no hay acceso anónimo ni registro).
2. `admin` ve **Administrar Jenkins**; `team-incidents` no lo ve.
3. Aparecen los 7 jobs; `team-incidents` puede pulsar **Scan Multibranch Pipeline Now** en `incidents` y no en `events`.
4. En **Administrar Jenkins → Credentials** aparecen `github-readonly` y `ghcr-push`.
5. En `events` → **Scan Multibranch Pipeline Log** aparece `Checking branches...` y `develop` con su `Jenkinsfile`.
6. En los logs no hay errores: `docker compose -f platform/deploy/local/compose.yaml --profile ci logs jenkins | grep SEVERE`.

## 6. Operación

| Tarea | Cómo |
|---|---|
| Cambiar usuarios, roles, jobs o plugins | Editar `casc.yaml` o `plugins.txt` → PR → `up -d --build` |
| Cambiar una contraseña o un token | Editar `.env` → `docker compose -f platform/deploy/local/compose.yaml --profile ci up -d jenkins` (recrea el contenedor) |
| Ver logs | `docker compose -f platform/deploy/local/compose.yaml --profile ci logs -f jenkins` |
| Apagar sin perder datos | `docker compose -f platform/deploy/local/compose.yaml --profile ci stop jenkins` (**sin** `-v`) |
| Actualizar Jenkins | Cambiar la versión en `Dockerfile` (y la de uv si hace falta) → PR → `up -d --build` |

### Respaldo y restauración

- **Configuración:** está en git. Restaurar = clonar el repo y `up -d --build`.
- **Secretos:** guarda una copia del `.env` en un gestor de contraseñas del equipo (no en el repo ni en Drive público).
- **Historial (opcional):** respaldar el volumen:

```bash
docker run --rm -v local_jenkins-home:/data -v "$PWD":/backup alpine \
  tar czf /backup/jenkins-home-$(date +%F).tgz -C /data .
```

Si se pierde el volumen, Jenkins se reconstruye igual desde el repo y el `.env`. Solo se pierde el historial de builds.

## 7. Mover Jenkins a una VM (cuando se decida D-19)

1. En la VM: instalar Docker, clonar el repo y copiar el `.env`.
2. Cambiar `JENKINS_URL` en `.env` a la URL pública (de preferencia HTTPS, detrás de un proxy inverso).
3. `docker compose -f platform/deploy/local/compose.yaml --profile ci up -d --build jenkins`.
4. Con URL pública, configurar en GitHub un **webhook** (`<JENKINS_URL>github-webhook/`, eventos *push* y *pull request*).
   El escaneo cada 2 minutos puede quedarse como respaldo o subirse a 15 minutos para gastar menos API.
5. **No exponer el puerto 8090 directo a internet sin HTTPS.**

## 8. Limitaciones conocidas (fase 2)

- **`make build` todavía no funciona dentro de Jenkins:** el contenedor no tiene motor de contenedores. Opciones a decidir:
  socket del host, Podman dentro del contenedor o un agente aparte. Mientras tanto, la etapa *Construir imagen* de los Jenkinsfile falla.
- Los builds corren en el nodo principal (`numExecutors: 2`). Con más carga conviene un agente separado.
- Escanear 7 jobs cada 2 minutos consume API de GitHub. `ThrottleForNormalize` frena antes de agotar el límite; con webhook desaparece el problema.

## 9. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| Jenkins no arranca y el log dice `Configuration as Code ... unresolved variable` | Falta una variable en `.env`. Compárala con `.env.example`. |
| El escaneo se queda en `Getting remote pull requests...` | Token de GitHub inválido o vencido. Revisa `GITHUB_TOKEN`. |
| Un plugin "no existe" al construir | Fin de línea CRLF en `plugins.txt`. La carpeta tiene `.gitattributes` con `eol=lf`; vuelve a sacar el archivo con `git checkout -- platform/deploy/jenkins/`. |
| `curl -X POST` a Jenkins devuelve 403 aunque el usuario tenga permiso | Jenkins exige un *crumb* (protección CSRF). Usa la interfaz o pide primero `/crumbIssuer/api/json`. |
| El puerto 8090 ya está ocupado | Cambia `"8090:8080"` en `platform/deploy/local/compose.yaml` y `JENKINS_URL` en `.env`. |

