# Trazabilidad de cimientos de Problems

Corte: 22 de noviembre de 2026. La evidencia operativa corresponde al commit
[45183f3](https://github.com/help-chair/help-chair/commit/45183f34544420348247468f7c1b0bef4814cbd5)
y está resumida en el [PR231](https://github.com/help-chair/help-chair/pull/231).
Son verificaciones locales sobre PostgreSQL 16.16, no resultados de Jenkins/CI.
Esta actualización de prosa no reejecuta la suite ni modifica backend o esquema.

| Criterio | Archivo o comando | Resultado local verificado |
|---|---|---|
| #110: entorno real | [environment.py](../config/environment.py), [inventario vacío](../.env.example), tests/test_runtime.py | Variables obligatorias, rechazo de SQLite/defaults y errores sin valores privados |
| #110: PostgreSQL y migraciones | problems/migrations/0001_initial.py; make migrate dos veces; migrate --check | Aplicación desde vacío, una migración inicial registrada, segunda sin pendientes |
| #110: salud y fallo BD | [views.py](../core/views.py), [compose.yaml](../compose.yaml) | Live200/ready503 al caer BD; recuperación200 sin reiniciar API; Compose2.22s |
| #110: contenedor y logs | [Dockerfile](../Dockerfile), gunicorn.conf.py, config/logging.py | Build sin secretos; UID10001/PID1; JSON; SIGTERM exit0/OOM=false en3.05s; persistencia |
| #110 y parte Problems de #135: calidad | [Makefile](../Makefile); make lint/test/build; tests/test_models.py (antes test_modelos.py); hooks explícitos | Exit0; 50 pruebas, cobertura informada95%; cuatro casos originales de modelo conservados; pre-commit Passed |
| #110: datos repetibles | [seed_demo.py](../problems/management/commands/seed_demo.py), tests/test_seed.py | Opt-in, repetición, filas ajenas, colisiones/rollback, concurrencia y secuencias sin rebobinar |
| #110 y parte Problems de #136: guía | [README bilingüe](../README.md), .env.example | Requisitos, alcance, puertos, entorno privado, migraciones, seed, salud y comandos documentados; diagrama de #13 conservado |
| #110: revisión y evidencia | PR231, commit45183f3 | Evidencia local publicada; aprobación de CODEOWNERS e integración aún pendientes |

También pasaron `makemigrations --check --dry-run`, `manage.py check` y
`git diff --check`. El escaneo controlado no encontró valores privados efímeros
en fuentes/metadatos ni en 11547 archivos de capas; detect-secrets comprobó los
21 blobs exactos del commit con cero hallazgos. No se publicaron valores de entorno,
DSN, cabeceras, credenciales, imágenes o datos reales. Recursos de ensayo retirados.

## Contribución coincidente y límites

Se contrastaron únicamente README y .env.example de Problems del
[PR205, commit8d17429](https://github.com/help-chair/help-chair/pull/205/commits/8d17429a0ad2babd9a9640417701487c1ab693fb).
Coinciden el alcance por servicio, referencias externas por ID, PostgreSQL propio,
puertos, comandos Make, endpoints operativos y documentación bilingüe. Se conservan
esos contenidos compatibles y el diagrama original. Las indicaciones de copiar/cargar
.env, clave ficticia/predeterminada y SQLite implícito de aquella propuesta no son
compatibles con la configuración estricta de #110; aquí rige el entorno real.
No se modificó PR205 ni se atribuye esa contribución a este incremento.

El [PR223 integrado](https://github.com/help-chair/help-chair/pull/223) establece
`/api/problems/v1` en el contrato de develop. Describe negocio previsto; esta rama
no añade CRUD, JWT o transiciones REST por documentarlo y conserva su snapshot
contractual. No se modifican modelos, migraciones, admin, contratos o dependencias.

#135/#136 abarcan ambos servicios: esta matriz acredita únicamente la porción de
Problems. La evidencia de Knowledge y la aceptación del equipo se revisan por sus
entregas propias. No se reasignan issues ni se afirma su cierre. Quedan la revisión
humana, las conversaciones/acuerdos pertinentes y el merge autorizado; no se requiere
una nueva funcionalidad de fases posteriores para acreditar estos cimientos.

## English

The table maps #110 and the Problems portion of #135/#136 to files, commands and
local evidence at commit45183f3: PostgreSQL16.16, 50 tests, lint/build/hooks and
operational checks. These are not CI results and were not rerun for prose edits.
PR205's compatible scope, database isolation, ports, Make commands and bilingual
documentation were compared read-only; its .env/default-key/implicit-SQLite advice
does not apply to the strict process environment. No contribution is reassigned.
Merged PR223 defines `/api/problems/v1` in develop's planned contract; backend
business endpoints are not implemented by this documentation. CODEOWNER approval,
team acceptance and authorized integration remain pending. This mapping neither
closes the issues nor certifies the Knowledge portion of the shared tasks.

## Conciliación con develop

PR205 ya integrado: se conservaron alcance, aislamiento, puertos, comandos y rutas
operativas compatibles, con la política confirmada de entorno real y PostgreSQL.
La resolución modifica solo README y el inventario vacío de variables de Problems;
los demás cambios entran desde develop sin edición manual de otros servicios.

Tras conciliar origin/develop (0842431), se repitieron las verificaciones en un
PostgreSQL16.16 privado nuevo: make lint, 50 pruebas (6.26s, cobertura95%), build,
migraciones desde vacío/repetidas y checks Django/drift correctos. La evidencia
actual se publica en el mismo PR231; no sustituye la aprobación humana.

After merging develop, the current isolated PostgreSQL16.16 run passed 50 tests,
lint/build, empty/repeated migrations and Django/drift checks. Evidence is local,
not CI; team approval remains pending.
