# Evidencia y cobertura documental de los cimientos de KB

Evidencia histórica del 22 de noviembre de 2026, previa a esta conciliación. Fuentes separadas:

- [Esquema/fixture, PR #228](https://github.com/help-chair/help-chair/pull/228),
  [commit 4f8573d](https://github.com/help-chair/help-chair/commit/4f8573d442de3c01a4f866d5468f3f4ac6e2d4ec).
- [Runtime y evidencia local, PR #229](https://github.com/help-chair/help-chair/pull/229),
  [commit a2bd10f](https://github.com/help-chair/help-chair/commit/a2bd10f4854ef572f2ae2b4439551452a2a222a3).
- [Contrato propuesto y validación, PR #230](https://github.com/help-chair/help-chair/pull/230),
  [commit 8666c03](https://github.com/help-chair/help-chair/commit/8666c03416c7862e470efaf5c7a273ec32c30087).

Los resultados siguientes se ejecutaron localmente en el incremento correspondiente;
esta actualización documental no repite suites ni los presenta como CI, aprobación
de consumidores o integración en develop. #228 y #230 ya están integrados en develop. La conciliación de #229 incorpora
esa base sin duplicar modelos ni contrato. La evidencia anterior sigue siendo
local e histórica; los resultados de esta ejecución se registran por separado.

| Issue / criterio | Evidencia ya registrada | Fuente y pendiente |
|---|---|---|
| #111: variables reales y sin secretos | Runtime sin read_env, defaults secretos o SQLite implícito; inventario vacío; regresiones de faltantes/bypass | a2bd10f, config/settings.py, config/environment.py y tests/test_runtime.py; valores privados fuera de Git |
| #111: PostgreSQL y migración inicial | PostgreSQL 16.16 vacío, migrate correcto, segunda sin pendientes y una sola articles.0001_initial | 4f8573d + ejecución de #229; no generar otra inicial |
| #111: contenedor y salud | Imagen y Compose propios; live 200/ready 503 con BD detenida, recuperación sin reiniciar API; en Compose fallo en 2.02 s | a2bd10f, compose.yaml/core/views.py; evidencia local, no despliegue global |
| #111: no root/gunicorn/JSON/SIGTERM | UID 10001, gunicorn PID 1, JSON saneado, parada exit 0 sin SIGKILL y persistencia | a2bd10f; build sin secretos y runtime con inyección privada |
| #111: lint/test/build y prueba significativa | make lint/test/build exit 0; 62 pruebas PostgreSQL, cobertura informada 94 %; regresiones de entorno/salud/logging/exportación | a2bd10f y cuerpo #229; no implica API de negocio implementada |
| #111: seed repetible | Sin opt-in exit 2 y sin escritura; dos cargas de kb_demo conservan UUID y otra fila de ensayo | Fixture 4f8573d + Makefile de a2bd10f; recarga sobrescribe sus ejemplos |
| #111: README operativo | Instalación, entorno, puertos, migraciones, seed, imagen, Compose y recuperación en ambos idiomas | README de a2bd10f; correspondencia contractual y revisión pendientes |
| #111: revisión/evidencia en PR | Evidencia local resumida publicada en #229; escaneos y recursos de ensayo retirados | #228 ya integrado; revisión de #229 y flujo de cierre siguen separados de esta evidencia |
| #135: parte Knowledge | make lint/test correctos; pruebas de modelos/admin/salud de #228 conservadas; pre-commit completo correcto en #229 | No acredita la mitad Problems ni cierra la issue de ambos servicios |
| #136: parte Knowledge | README completo en español/inglés y PostgreSQL/API 8006/BD host 5446 documentados | No acredita la mitad Problems ni sustituye revisión de #205; sin cierres/asignaciones automáticos |

El esquema de #228 registra previamente 39 pruebas en PostgreSQL. La suite de
#229 registra 62 pruebas, incluidas las anteriores; no sumar ambas como suites
disjuntas. El contrato de #230 registra 41 ejemplos, 37 negativos, cuatro artículos
de fixture y 16 comprobaciones Prism; no sumarlos al conteo pytest ni describirlos
como consultas reales de API/BD/JWT.

La porción Problems de #135/#136 se documenta por separado en
[PR #231](https://github.com/help-chair/help-chair/pull/231), con seguimiento
[5aff326](https://github.com/help-chair/help-chair/commit/5aff32665cbb35d1037d83a74976be7737c1d2e3).
Su cuerpo registra 50 pruebas locales PostgreSQL, lint/build/hooks correctos y
README bilingüe. Son resultados del frente #110, no ejecutados por este cambio
documental de KB. Las dos contribuciones aportan cobertura técnica de ambos
servicios; revisión humana, integración y cierre de las issues siguen pendientes.

### Conciliación documental con PR #205

Referencia: [README propuesto 8d17429](https://github.com/help-chair/help-chair/blob/8d17429a0ad2babd9a9640417701487c1ab693fb/services/knowledge/README.md).
PR #205 ya está integrado. Se conserva su contenido compatible sin editarlo, no se atribuye su trabajo a otra
persona ni se modifican responsables o estados de #135/#136.

| Contenido de #205 | Tratamiento compatible con #229 y la política vigente |
|---|---|
| Responsabilidades, consumidores y BD independiente | Conservar: KB almacena conocimiento, se consume por API y no registra errores de Problemas ni decide aplicabilidad |
| Python/Django/DRF, PostgreSQL, puertos y equivalencia bilingüe | Conservar esos datos, ya incluidos en #229 |
| Activación de venv sin uv | Puede explicarse como ayuda opcional; no afirmar que macOS se haya probado en #229 |
| Creación/carga de .env y SQLite por omisión | No trasladar: #229 usa entorno real obligatorio y PostgreSQL explícito |
| Clave de desarrollo/defaults y valores de configuración de ejemplo | No trasladar: secretos fuera de Git y documentación sin valores; .env.example solo nombres vacíos |
| make up global o Compose global con configuración incrustada | Usar el Compose propio del servicio, sin .env implícito y con proveedor privado verificado; no modificar Plataforma aquí |
| make openapi como exportación al contrato canónico | No trasladar: OPENAPI_OUTPUT debe ser explícito fuera de contracts/; #230 usa su propio validador |
| Búsqueda/API descritas como disponibles y “no autentica usuarios” | Distinguir capacidad prevista de implementación. Accesos emite identidad; KB deberá validar el contexto cuando se implemente su API |
| Evidencia macOS de siete pruebas Problems/tres Knowledge | Es una declaración histórica del cuerpo de #205, no la ejecución PostgreSQL de #229 ni evidencia actual de ambos servicios |

### Límites de entrega

No hay nueva implementación de modelo para #133, ni CRUD/búsqueda/JWT por esta
documentación. Se mantienen pendientes las revisiones reales del equipo y
consumidores. Este registro permite avanzar con la contribución técnica sin
esperar esas revisiones, pero no las sustituye ni autoriza merge/cierre.

### Conciliación con develop

La base `0842431c7b401b2bb21e9336702a8487565d165d` integra #205, #230 y #228.
Esta resolución mantiene PostgreSQL obligatorio en local, pruebas, CI y producción;
SECRET_KEY obligatoria incluso con DEBUG/pytest y ausencia de autocarga de .env.
Conserva de #205 responsabilidades, clientes previstos, puertos, rutas actuales y
documentación bilingüe, sin recuperar sus instrucciones antiguas de configuración.
Modelos, admin, migración, fixture y pruebas del esquema conservan los blobs de
la base integrada; no se crea otra migración ni se altera el dominio.

Verificación actual posterior a la conciliación: 62 pruebas en PostgreSQL 16.16,
make lint/test/build correctos, check de Django y drift sin incidencias, migración
desde vacío y segunda aplicación sin pendientes, seed con opt-in repetible y fila
ajena conservada. Estas ejecuciones son locales y distintas del corte histórico
anterior; no se atribuyen a CI ni a una aprobación de consumidores.

También se verificaron imagen y Compose propio: UID 10001 y Gunicorn como PID 1,
live 200/ready 503 sin BD y recuperación, SIGTERM con salida 0 sin OOM,
reinicio con persistencia y migración única. Pre-commit pasó sobre los archivos
conciliados. El escaneo de código, metadatos y 11543 archivos de capas no encontró
los secretos efímeros del ensayo ni archivos privados de configuración.
