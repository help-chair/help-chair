# Plan de fases — Help Chair

> Calendario de 25 días (13 de noviembre – 7 de diciembre de 2026) para entregar Help Chair **funcionando, accesible y desplegado en la nube**, con contenedores (Podman), Kubernetes, CI/CD con Jenkins, backend en Django y frontend en React. Participan 7 equipos y 17 personas.

*Este documento está en español. La versión en inglés queda pendiente.*

## 1. Calendario y puertas de salida

| Fase | Nombre | Fechas | Qué debe quedar demostrable | Etiqueta Git |
|---|---|---|---|---|
| **1** | Cimientos | 13 – 17 nov | Cada servicio corre en Podman con su BD; contratos v0; plantilla y entorno listos | `fase-1` |
| **2** | Núcleo de servicios | 18 – 22 nov | Cada servicio funciona solo (API + BD + pruebas); CI/CD publica imágenes; contratos v1 congelados | `fase-2` |
| **3** | Integración y despliegue de testing | 23 – 27 nov | El flujo completo funciona y está **desplegado en la nube (testing)** con CD automático | `fase-3` |
| **4** | Multiempresa, robustez y alcance extendido | 28 nov – 2 dic | Alta de empresa → stack nuevo y aislado; seguridad, carga y accesibilidad verificadas | `fase-4` |
| **5** | Estabilización y entrega | 3 – 7 dic | Producción desplegada, documentación completa, demo y release v1.0.0 | `fase-5` |

Cada fase termina con una **puerta de salida**: algo que se puede mostrar corriendo, no solo «avance». Si una puerta no se cumple, la siguiente fase empieza cerrándola. Al cumplirla se fusiona `develop` → `main` y se etiqueta `fase-N`.

## 2. Ritmo de trabajo (se repite en cada fase)

| Cuándo | Qué pasa |
|---|---|
| Día 1 | Planeación: crear issues y milestone de la fase, repartir trabajo, acordar contratos que se tocan. |
| Días 2–3 | Desarrollo con PR pequeños (< 400 líneas), revisión en menos de 24 h. |
| Día 4 | Integración con otros equipos, pruebas, corrección de lo que falle, documentación. |
| Día 5 | Demo de cada equipo (5 min), revisión de la puerta de salida, merge `develop` → `main`, etiqueta `fase-N` y retrospectiva corta. |

**Reglas del ritmo**

- Todo cambio entra por Pull Request a `develop`, con revisión del dueño de la carpeta (ver [`CONTRIBUTING.md`](../CONTRIBUTING.md)).
- Cada fase tiene un **milestone** en GitHub y un issue por entregable de las tablas.
- Cada fase deja **evidencia verificable en GitHub**: código fusionado, pruebas pasando, documentación y etiqueta.
- Máximo 2 PR abiertos por persona; los PR viejos bloquean a los demás.
- Sincronización diaria breve y asíncrona en el canal del proyecto (qué hice, qué haré, qué me bloquea).

**Roles sugeridos dentro de cada equipo** (con 2 o 3 personas por equipo, una persona puede tener más de un rol)

| Rol | Responsabilidad |
|---|---|
| Líder técnico | Decide arquitectura interna, revisa PR críticos y representa al equipo en los acuerdos de contratos. |
| Responsable de pruebas (QA) | Cuida cobertura, pruebas de contrato e integración y el estado del CI. Puede rotar por fase. |
| Responsable de documentación | Mantiene README del servicio, OpenAPI y runbooks al día. Puede rotar por fase. |
| Desarrolladores | Reparten funcionalidades por verticales (modelo + API + pruebas), no por capas. |

## 3. Ambientes

| Ambiente | Dónde | Cómo se despliega | Disponible | Datos |
|---|---|---|---|---|
| Desarrollo (dev) | Local, con `podman compose` | Cada persona | Desde la fase 1 | Datos de ejemplo (`make seed`) |
| Testing | Nube, namespace `testing` | Se despliega solo al fusionar en `develop` (Jenkins) | Desde la fase 3 | Datos de prueba; se puede apagar fuera de horario |
| Producción | Nube, namespace por empresa | Etiqueta en `main` + aprobación manual en Jenkins | Fase 5 (ensayo en fase 4) | Datos reales de la demo |

## 4. Estándares técnicos por defecto

| Área | Herramientas |
|---|---|
| Backend (todos) | Python 3.12, Django 5 + Django REST Framework, `drf-spectacular` (OpenAPI), `djangorestframework-simplejwt`, `django-environ`, gunicorn |
| Base de datos | PostgreSQL en contenedor, **una por servicio** (cada equipo la suya) |
| Pruebas backend | `pytest-django`, `factory_boy`, `coverage`, `schemathesis` (contratos) |
| Calidad | `ruff`, `pre-commit`, Conventional Commits, PR con CODEOWNERS |
| Frontend | React + Vite + TypeScript, ESLint/Prettier, Vitest + Testing Library, Playwright (E2E), axe/Lighthouse (accesibilidad) |
| Contenedores | Podman (build y `podman compose` local); imágenes OCI estándar |
| Orquestación | Kubernetes + Helm, ingress-nginx, cert-manager |
| CI/CD | Jenkins (multibranch, un `Jenkinsfile` por servicio, ejecución filtrada por carpeta) |
| Registro de imágenes | GitHub Container Registry (propuesto) o el de la nube elegida |
| Mensajería | Broker ligero por stack (NATS o RabbitMQ, a decidir en la fase 1) |
| Seguridad / carga | OWASP ZAP (baseline), Trivy (imágenes), `pip-audit`/`npm audit`, k6 |

## 5. Fase 1 — Cimientos y diseño (13 – 17 de noviembre)

**Objetivo:** Que los 7 equipos tengan el mismo punto de partida técnico y que todo servicio ya arranque, aunque todavía no haga nada útil.

> ⚠️ Hoy es 14 de noviembre: si el equipo va atrasado, la prioridad absoluta es (1) plantilla Django, (2) `podman compose` y (3) contratos v0. Figma puede arrancar con wireframes de 5 pantallas.

### Entregables por equipo

| Equipo | Entregables | Evidencia en GitHub |
|---|---|---|
| Todos los equipos de backend | • Proyecto Django + DRF dentro de su carpeta, con ajustes por entorno (`django-environ`)<br>• Conexión a **su** PostgreSQL y migración inicial aplicada<br>• `/health/live` y `/health/ready` (este último verifica la BD)<br>• `Dockerfile` (usuario no root, gunicorn) y `Makefile` (`make run`, `test`, `lint`, `build`, `seed`)<br>• `.env.example`, `ruff` + `pre-commit`, `pytest` con una prueba pasando<br>• README del servicio completo (cómo correrlo en local) | PR a `develop` por servicio con la estructura; `make test` en verde |
| Eventos | • Modelo de datos (evento, clasificación, prioridad, estado) y diagrama entidad-relación<br>• Las 9 reglas de destino escritas como **pruebas parametrizadas** (TDD: aún pueden fallar)<br>• Borrador OpenAPI y esquema del mensaje común de eventos | `services/events/` con modelos y migraciones; `contracts/events/openapi.yaml`; `contracts/messages/` |
| Accesos | • Modelos de usuario, rol, perfil y departamento<br>• Login básico con JWT (claims: empresa, rol, expiración)<br>• Catálogo de eventos de seguridad que emitirá | `services/access/` con login funcionando en local; OpenAPI v0 |
| Peticiones | • Modelo de petición, catálogo de servicios solicitables y estados ITIL<br>• Borrador OpenAPI | `services/requests/` con modelos, admin de Django y OpenAPI v0 |
| Incidencias | • Modelo de incidente, estados ITIL y matriz de prioridad (impacto × urgencia)<br>• Borrador OpenAPI | `services/incidents/` con modelos, admin de Django y OpenAPI v0 |
| Problemas + KB | • Modelos de problema, error conocido y artículo de la KB<br>• Borrador OpenAPI de ambos servicios | `services/problems/` y `services/knowledge/` con modelos y OpenAPI v0 |
| Frontend | • Diseños en Figma (login, onboarding, tablero, tickets, KB); enlace en el repo<br>• Proyecto React + Vite + TypeScript con lint, formato, pruebas (Vitest) y estructura de carpetas<br>• Cliente de API y **servidor de mocks** a partir de los OpenAPI (Prism)<br>• `Dockerfile` del frontend | `frontend/` corriendo con `npm run dev`; capturas de Figma en `docs/design/` |
| Plataforma | • **Plantilla de servicio Django** lista el día 1–2 (para que los 6 backends nazcan iguales)<br>• `podman compose` local: una BD por servicio, broker y buzón de correo de pruebas (Mailpit)<br>• Jenkins instalado en una VM y `Jenkinsfile` plantilla<br>• Decisión de nube, Kubernetes y registro de imágenes (documentada)<br>• Esqueleto del gateway (`Tenant` y resolución de subdominio) | `platform/templates/django-service/`, `platform/deploy/local/compose.yaml`, `Jenkinsfile`, ADR en `docs/` |
| Pruebas (transversal) | • `docs/TESTING.md`: pirámide de pruebas, metas de cobertura, herramientas y convenciones<br>• Una prueba unitaria por servicio corriendo en `make test` | `docs/TESTING.md` y pruebas en cada carpeta |

**Pruebas de la fase:** Configuración de `pytest`, `ruff` y Vitest; primera prueba por servicio; validación de los OpenAPI con `openapi-spec-validator`.

### Riesgos y plan B

| Riesgo | Alternativa |
|---|---|
| La plantilla de Django se retrasa y los equipos esperan | Cada equipo usa `django-admin startproject` con una guía de 10 pasos en el README y migra a la plantilla después. |
| Jenkins no queda listo a tiempo | Todo lo que hará el pipeline ya existe como `make lint test build`; se corre a mano y Jenkins llega en la fase 2. |
| `podman compose` no se comporta igual que Docker Compose | Usar el formato estándar Compose Spec y probar en Fedora; alternativa `podman kube play` con manifiestos. |
| Figma tarda más de lo previsto | Wireframes de baja fidelidad de 5 pantallas bastan para empezar; el pulido visual pasa a la fase 4. |

**✅ Puerta de salida:** Cada servicio arranca con `make run` y `podman compose up`, `/health/ready` responde OK, hay PR fusionados en `develop` de todos los equipos y los contratos v0 están revisados por quienes los consumirán.


## 6. Fase 2 — Núcleo de cada servicio (18 – 22 de noviembre)

**Objetivo:** Que cada servicio funcione por sí solo (API, BD y pruebas) y que el pipeline construya y publique su imagen. Al cerrar, **se congelan los contratos v1**.

### Entregables por equipo

| Equipo | Entregables | Evidencia en GitHub |
|---|---|---|
| Eventos | • Registro de eventos (usuario o sistema), filtrado y **deduplicación con contador**<br>• Clasificación (informativo, advertencia, excepción) y prioridad con matriz e importancia del servicio<br>• Estados del ciclo de vida y cierre automático de eventos informativos<br>• Publicación de eventos al broker con patrón *outbox* simple | `services/events/` con endpoints, pruebas (≥ 60 %) y OpenAPI v1 generado con `drf-spectacular` |
| Accesos | • Registro, login, refresh de token y roles con permisos<br>• Bloqueo por intentos fallidos de login<br>• Emisión de eventos de login (exitoso, fallido, forzado) | `services/access/` con pruebas y OpenAPI v1 |
| Peticiones | • CRUD de peticiones, catálogo, estados y asignación<br>• Consumidor de eventos (`manage.py consume_events`) | `services/requests/` con pruebas y OpenAPI v1 |
| Incidencias | • CRUD de incidentes, estados, prioridad, asignación y escalamiento manual<br>• Consumidor de eventos | `services/incidents/` con pruebas y OpenAPI v1 |
| Problemas + KB | • CRUD de problemas; vínculo a incidentes **por ID** (nunca por llave foránea entre BD)<br>• KB: artículos y búsqueda (full-text de PostgreSQL); error conocido | `services/problems/` y `services/knowledge/` con pruebas y OpenAPI v1 |
| Frontend | • Login, layout, navegación según rol<br>• Listas y detalle de tickets contra los **mocks** (estados de carga, vacío y error)<br>• Componentes accesibles y pruebas con Testing Library | `frontend/` con pantallas funcionando y pruebas; Storybook opcional |
| Plataforma | • `Jenkinsfile` por servicio: lint → test → build → push de la imagen (etiqueta = SHA del commit)<br>• Multibranch con ejecución filtrada por carpeta<br>• Broker definitivo en el compose<br>• Chart de Helm base del stack (servicios + BD + broker) y clúster de Kubernetes accesible para todos<br>• Gateway resolviendo subdominio → empresa en local | `platform/deploy/helm/stack/`, `Jenkinsfile` en cada servicio, imágenes visibles en el registro |
| Pruebas (transversal) | • Pruebas de contrato: cada servicio contra su OpenAPI (`schemathesis`)<br>• Cobertura reportada en Jenkins | `tests/contract/` o carpeta de pruebas de cada servicio; badge de CI en el README |

**Pruebas de la fase:** Unitarias en los 6 backends (meta orientativa 60 % de lo propio), pruebas de contrato, pruebas de componentes en el frontend.

### Riesgos y plan B

| Riesgo | Alternativa |
|---|---|
| El broker se complica con Django | Plan B: REST síncrono con reintentos y *outbox* en BD; la interfaz del cliente es la misma, así se cambia después sin tocar la lógica. |
| Cambios de modelo rompen a otros equipos | Migraciones versionadas (jamás editar una ya fusionada) y contratos v1 congelados al cierre de la fase. |
| Los agentes de Jenkins son lentos | PR corren solo lint y pruebas rápidas; construir imágenes solo en `develop` y en etiquetas. |
| Un equipo se atrasa y bloquea a los demás | Los otros trabajan contra mocks de Prism generados del OpenAPI; el atraso no frena la integración de los demás. |

**✅ Puerta de salida:** El stack completo corre con `podman compose` y datos de ejemplo, los pipelines están en verde, las imágenes están en el registro y los contratos v1 quedan congelados (etiqueta `contracts-v1`).


## 7. Fase 3 — Integración y despliegue de testing (23 – 27 de noviembre)

**Objetivo:** Conectar los servicios entre sí, quitar los mocks y **desplegar el stack completo en la nube (ambiente de testing)** con despliegue continuo desde `develop`.

> ⚠️ Aquí se prueba por primera vez toda la cadena: código en GitHub → Jenkins → imagen → Kubernetes → URL pública. Es mejor que falle ahora que en la fase 5.

### Entregables por equipo

| Equipo | Entregables | Evidencia en GitHub |
|---|---|---|
| Eventos | • Enrutamiento real de las 9 reglas hacia Peticiones, Incidencias, Problemas y Accesos<br>• Auto-respuesta consultando la KB (timeout y degradación si la KB no responde)<br>• Triage manual y asignación con notificación al usuario | PR con integración y pruebas de integración; reglas 1–9 en verde |
| Accesos | • Los demás servicios validan el JWT con la **clave pública** de Accesos<br>• Eventos de credenciales llegan a Eventos y se clasifican como seguridad | PR en `services/access/` y en cada servicio consumidor (solo su parte) |
| Peticiones e Incidencias | • Flujo de extremo a extremo: nuevo → asignado → en proceso → resuelto → cerrado (+ reabierto)<br>• Cierre con **encuesta de satisfacción**; motivos al cancelar<br>• Fecha objetivo de SLA calculada por prioridad | PR con el flujo y pruebas de integración |
| Problemas + KB | • Detección de patrones: mismo patrón N veces en T días → problema (tarea programada)<br>• Registro de uso de artículos y botón «no me sirvió» | PR con la tarea programada, pruebas y OpenAPI al día |
| Frontend | • Todas las pantallas contra las **APIs reales**<br>• Asistente de onboarding (servicios e importancia, prioridades, SLA, departamentos, usuarios)<br>• Vistas de ticket, KB y encuesta<br>• Prueba E2E del camino feliz con Playwright | `frontend/` sin mocks; `tests/e2e/` con la prueba |
| Plataforma | • **Despliegue de testing** en la nube: namespace `testing` con un stack, ingress y TLS (cert-manager), DNS wildcard<br>• Despliegue continuo: fusionar en `develop` → Jenkins despliega y corre *smoke tests*<br>• Secretos en Kubernetes Secrets; respaldo con `pg_dump` en un CronJob<br>• Runbook de despliegue | `platform/deploy/helm/`, `Jenkinsfile` de despliegue, `docs/runbooks/deploy-testing.md`, URL de testing en el README |
| Pruebas (transversal) | • Pruebas de integración entre servicios en CI (con `podman compose`)<br>• E2E del camino feliz en Jenkins contra testing<br>• `make seed` con datos de prueba repetibles | Resultados visibles en Jenkins y capturas en `docs/reports/` |

**Pruebas de la fase:** Integración entre servicios, E2E del flujo login → evento → clasificación → ticket → cierre con encuesta, smoke tests posteriores al despliegue.

### Riesgos y plan B

| Riesgo | Alternativa |
|---|---|
| Costo o cuota de la nube se agota | Clúster **k3s en una o dos VM** en lugar del servicio administrado, y apagar testing fuera de horario (`make testing-down`). |
| DNS o certificados tardan | Usar subdominios `nip.io` / `sslip.io` con certificado autofirmado en testing; el dominio real y TLS definitivo se hacen en la fase 4. |
| La integración rompe servicios que ya funcionaban | Interruptores por variable de entorno (`USE_REAL_KB`, `USE_BROKER`) para volver al comportamiento aislado mientras se corrige. |
| Nadie puede ver el ambiente por falta de acceso | Guía de acceso (kubeconfig de solo lectura por equipo) y URL pública en el README. |

**✅ Puerta de salida:** Una empresa de ejemplo usa el help desk completo en la **URL de testing**, el E2E está en verde en Jenkins, se registró el recorrido (video o GIF) en `docs/` y se etiqueta `fase-3`.


## 8. Fase 4 — Multiempresa, robustez y alcance extendido (28 de noviembre – 2 de diciembre)

**Objetivo:** Que el alta de una empresa cree su stack aislado de forma automática, que el producto sea seguro y accesible y que entren las funciones que parecían fuera de alcance en su versión mínima.

> ⚠️ Día 4 (1 de diciembre): *bug bash* de todo el proyecto y ensayo general en un ambiente con la forma de producción.

### Entregables por equipo

| Equipo | Entregables | Evidencia en GitHub |
|---|---|---|
| Plataforma | • Directorio de empresas con alta y subdominio; **aprovisionamiento automático** (namespace + Helm + migraciones + usuario administrador inicial)<br>• Gateway: login central → redirección al subdominio de la empresa<br>• `NetworkPolicy` de denegación por defecto, `ResourceQuota` y `LimitRange`<br>• Suspender y reactivar un stack (escala a 0 / 1)<br>• Perfil **Lite** opcional (`DB_ENGINE=sqlite`) para empresas de demostración<br>• Dominio propio del cliente: campo en el directorio, Ingress adicional y cert-manager | `platform/gateway/`, `platform/deploy/` y `docs/runbooks/alta-empresa.md` |
| Accesos | • Resolución de empresa por dominio del correo y emisión del token dentro del stack<br>• Invitación de usuarios por correo<br>• SSO con Google (OIDC), como mejora opcional | PR en `services/access/` con pruebas |
| Eventos | • Configuración de catálogo de servicios, importancia, matriz de prioridad y SLA (API)<br>• Ingesta de eventos de sistema por webhook con clave de API<br>• Alertas al superar el umbral de recurrencia<br>• SLA con horario laboral y festivos (opcional) | PR en `services/events/` con pruebas |
| Peticiones | • Tipo «cambio» con aprobación simple: pendiente → aprobado → implementado (Change Enablement mínimo)<br>• Aprobador definido en el onboarding | PR en `services/requests/` con pruebas |
| Incidencias | • Alertas de vencimiento de SLA y escalamiento automático<br>• Notificaciones por correo (`send_mail`, Mailpit en testing) | PR en `services/incidents/` con pruebas |
| Problemas + KB | • Errores conocidos vinculados a artículos y sugerencias al abrir un incidente<br>• Métricas simples de uso de la KB | PR en `services/problems/` y `services/knowledge/` |
| Frontend | • Pulido visual, diseño responsivo, manejo de errores<br>• Accesibilidad WCAG 2.1 AA (teclado, contraste, etiquetas) con puntaje de Lighthouse ≥ 90<br>• Panel de administración de la empresa (usuarios, SLA, servicios) | `frontend/` y reporte de accesibilidad en `docs/reports/` |
| Pruebas (transversal) | • E2E multiempresa: la empresa A **no** ve nada de la B<br>• Seguridad: OWASP ZAP baseline, Trivy en imágenes, `pip-audit` y `npm audit`<br>• Carga básica con k6 (50 usuarios virtuales) y revisión de accesibilidad<br>• *Bug bash* del proyecto completo | `tests/e2e/`, `tests/load/` y reportes en `docs/reports/` |

**Pruebas de la fase:** Aislamiento entre empresas, seguridad, carga y accesibilidad. Cada hallazgo grave se abre como issue con etiqueta `prioridad:alta`.

### Riesgos y plan B

| Riesgo | Alternativa |
|---|---|
| El aprovisionamiento automático es más difícil de lo estimado | Versión semi-automática: `make tenant-create EMPRESA=...` (o un job parametrizado de Jenkins) que ejecuta `helm install` y una lista de verificación; se automatiza después. |
| El CNI del clúster no aplica `NetworkPolicy` | Verificar al inicio de la fase; si no aplica, activar el soporte del proveedor o instalar Calico/Cilium. Respaldo: un namespace por empresa más pruebas E2E de aislamiento. |
| Falta memoria para varios stacks | Perfil Lite con SQLite, límites bajos de recursos y suspender las empresas que no se usan. |
| SSO, correo o SLA con calendario se complican | Se omiten sin afectar el producto: correo/contraseña ya funciona, notificaciones dentro de la app y SLA 24×7. |
| Hay demasiados hallazgos de seguridad o accesibilidad | Priorizar los graves; el resto queda como backlog v1.1 en GitHub Projects. |

**✅ Puerta de salida:** Se da de alta una empresa nueva y su stack aparece solo, vacío y aislado en menos de 10 minutos; el E2E de aislamiento pasa; los reportes están en `docs/reports/`; se etiqueta `fase-4`.


## 9. Fase 5 — Estabilización y entrega (3 – 7 de diciembre)

**Objetivo:** Congelar funcionalidades, estabilizar, documentar y entregar en producción con una demo ensayada.

> ⚠️ Días 1–2: **congelamiento de funcionalidades**; solo se corrigen bugs. Día 4: la documentación queda completa antes de la comida.

### Entregables por equipo

| Equipo | Entregables | Evidencia en GitHub |
|---|---|---|
| Todos los equipos de backend | • Regresión completa y corrección de bugs<br>• README del servicio, OpenAPI publicado (Swagger/Redoc) y decisiones (ADR) al día<br>• Cobertura final, limpieza de issues y PR abiertos<br>• Etiqueta `<servicio>/v1.0.0` y GitHub Release con notas | Etiquetas por servicio, Releases y `docs/` actualizados |
| Plataforma | • **Despliegue a producción** con aprobación manual en Jenkins<br>• Respaldos con restauración probada y monitoreo mínimo (health checks, `metrics-server`, Uptime Kuma o similar)<br>• Runbooks: alta de empresa, rollback, escalado, suspensión de stack<br>• Rollback ensayado a la imagen anterior (etiquetas por SHA) | `docs/runbooks/` y etiqueta `v1.0.0` en `main` |
| Frontend | • Guía de usuario con capturas, revisión final de accesibilidad, build de producción | `docs/user-guide/` y `frontend/` en `main` |
| Pruebas (transversal) | • **Pruebas de aceptación** (UAT) hechas por personas ajenas al equipo, con guion de unos 30 casos<br>• *Smoke tests* en producción y ensayos de la demo (mínimo 2) | Guion y resultados en `docs/reports/uat.md` |
| Proyecto (todos) | • Guion de la demo y video corto de respaldo<br>• Retrospectiva del proyecto<br>• Backlog v1.1 con lo que quedó fuera, en GitHub Projects | `docs/demo.md`, video enlazado y milestone `v1.1` |

**Pruebas de la fase:** Regresión completa, UAT, smoke tests en producción, repaso del recorrido de la demo.

### Riesgos y plan B

| Riesgo | Alternativa |
|---|---|
| Aparece un bug crítico el último día | Rollback a la imagen anterior y demo desde testing; el bug entra a `v1.0.1`. |
| Producción no está lista a tiempo | Demo sobre testing con datos de ejemplo y la guía de despliegue a producción documentada. |
| La documentación llega tarde | Responsable de documentación por equipo desde la fase 1 y el día 4 reservado solo para eso. |
| Se cae la conexión o la nube durante la demo | Video de respaldo y recorrido local con `podman compose`. |

**✅ Puerta de salida:** Demo completa en producción, documentación publicada, `v1.0.0` publicado como Release y etiqueta `fase-5`.


## 10. Alcance extendido y alternativas

Estas funciones empezaron como «fuera de alcance». Entran al plan en una versión mínima, con una alternativa si no alcanza el tiempo.

| Función | Dónde entra | Versión mínima | Si no alcanza |
|---|---|---|---|
| Change Enablement | Fase 4 · Peticiones | Tipo «cambio» con aprobación simple (pendiente → aprobado → implementado) | Solo la etiqueta `tipo=cambio` sin aprobación; el resto queda documentado como v1.1 |
| Dominio propio del cliente | Fase 4 · Plataforma | Campo en el directorio, Ingress adicional y cert-manager | Procedimiento manual en un runbook y una sola demostración |
| SSO | Fase 4 · Accesos | Login con Google (OIDC) | Se mantiene correo/contraseña; el diseño del SSO queda en `docs/` |
| Hibernación de stacks | Fase 4 · Plataforma | Acciones suspender y reactivar (escala a 0 / 1) por empresa | Límites bajos de recursos y comando manual `make tenant-suspend` |
| Notificaciones por correo | Fase 4 · Eventos e Incidencias | `send_mail` con plantillas; Mailpit en testing y SMTP en producción | Notificaciones dentro de la aplicación (campana) y bitácora |
| SLA con calendario laboral | Fase 4 · Eventos | Horario laboral y festivos por empresa | SLA 24×7 simple por prioridad |
| Perfil Lite | Fase 4 · Plataforma | `DB_ENGINE=sqlite` para empresas de demostración (sigue habiendo una BD por servicio) | Mantener PostgreSQL con límites de recursos más bajos |

## 11. Riesgos transversales y alternativas

| Riesgo | Mitigación y plan B |
|---|---|
| Jenkins se atora o necesita URL pública | Los *webhooks* de GitHub requieren que Jenkins sea alcanzable; si no, usar sondeo del repositorio (*Poll SCM*) cada 2 minutos. Todo paso del pipeline existe como `make ...`, por lo que se puede correr a mano. |
| Costo y memoria (6 Django + 6 BD + broker por empresa) | Límites de CPU/RAM desde la fase 2, gunicorn con pocos *workers*, imágenes `slim`, perfil Lite y suspensión de stacks. Medir consumo real en la fase 3. |
| Podman y Kubernetes | Las imágenes son OCI estándar y funcionan en Kubernetes. Si Podman da problemas en el agente de Jenkins, construir con otro motor compatible sin tocar los Dockerfile. |
| Dependencias entre equipos | Contratos v1 congelados al cierre de la fase 2, mocks con Prism y regla de que quien cambia un contrato avisa por PR a los consumidores. |
| Desgaste con 17 personas y varias horas diarias | Límite de trabajo en curso: máximo 2 PR abiertos por persona; sin trabajo nocturno el día de la demo; un descanso de media jornada tras cada puerta de salida. |
| Dependencia de una sola persona (*bus factor*) | Dos personas conocen cada componente crítico (gateway, aprovisionador, Accesos, Eventos) y la documentación vive en el repo. |
| Conflictos de merge en `develop` | PR pequeños, actualizar la rama a diario y `git add <carpeta>` en vez de `git add .`. |

## 12. Decisiones pendientes

| Decisión | Fecha límite | Notas |
|---|---|---|
| Broker (NATS o RabbitMQ) | Fase 1, día 3 | NATS es más ligero; RabbitMQ es más conocido con Django. Con Django, el consumidor corre como `manage.py consume_events`. |
| Nube (Azure, AWS o Google Cloud) | Fase 1, día 2 | Revisar créditos educativos vigentes y cuota de VM. |
| Kubernetes administrado o k3s en VM | Fase 1, día 3 | Administrado: menos operación, más costo. k3s: más barato, lo administramos nosotros. |
| Registro de imágenes | Fase 1, día 3 | GitHub Container Registry o el de la nube. |
| Verificación de JWT entre servicios | Fase 2, día 1 | Clave pública publicada por Accesos (recomendado). |
| Servidor SMTP real | Fase 4, día 1 | Solo si se hacen las notificaciones por correo. |
| Dominio del proyecto | Fase 3, día 1 | Necesario para DNS wildcard y certificados. |

## 13. Convenciones de seguimiento en GitHub

| Elemento | Convención |
|---|---|
| Milestones | Uno por fase: `Fase 1` … `Fase 5` (+ `v1.1` para lo pendiente). |
| Etiquetas (labels) | `fase:1`…`fase:5`, `area:events`, `area:access`…, `tipo:feature\|bug\|docs\|test\|infra`, `prioridad:alta\|media\|baja`. |
| Issues | Un issue por entregable de la tabla, asignado a una persona, con la evidencia esperada como criterio de aceptación. |
| Etiquetas Git | Por servicio: `events/v0.1.0` … ; por fase: `fase-N` sobre `main` al cerrar la puerta de salida. |
| Project (tablero) | GitHub Projects con columnas Pendiente · En curso · En revisión · Hecho, filtrable por equipo y fase. |

---
Centro de Enseñanza Técnica Industrial (CETI)