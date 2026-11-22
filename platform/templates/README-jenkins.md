# CI por servicio con Jenkins — #86

La plantilla ejecuta lint → pruebas → construcción de imagen mediante Make.
La imagen queda en el motor del agente; publicar imágenes corresponde a #88.
Construir una imagen no arranca el servicio ni despliega un entorno.

## Archivos y filtro

- `Jenkinsfile.template`: sustituir todas las apariciones de `__SERVICE__`.
- `../../services/events/Jenkinsfile`: copia de referencia para el multibranch.
- Los comandos de aplicación son `make lint`, `make test` y
  `make build TAG="$GIT_COMMIT"`, dentro de `services/<servicio>`.

`Checkout` obtiene la revisión del job y su changelog una sola vez.
La etapa padre `CI del servicio` aplica `when { changeset }` con GLOB sensible
a mayúsculas: `services/<servicio>/**`. Sus etapas hijas son secuenciales:
un fallo de lint impide Test/Build; un fallo de pruebas impide Build.

Excepciones explícitas al filtro:

1. El build número 1 de cada job hijo ejecuta CI aunque el changelog esté vacío.
2. `FORCE_CI=true` solicita CI manualmente. Su valor predeterminado es `false`.

En builds posteriores, sin cambios propios y con `FORCE_CI=false`, CI se omite.
El job todavía puede arrancar, reservar agente y hacer checkout; el filtro no
desactiva los disparadores. Se considera todo el changelog, no solo el último
commit. Cambiar la plantilla compartida no actualiza ni activa las copias:
hay que adaptar cada Jenkinsfile y revisar su cambio con el equipo propietario.

## Agente y configuración

`agent any` conserva el comportamiento del ejemplo original de Eventos.
Plataforma debe garantizar que los nodos elegibles sean Linux y dispongan de:
Git, GNU Make, `uv`, Python 3.12 instalado u obtenible por `uv`, y un motor OCI
operativo para el usuario del agente. También necesita workspace escribible
y acceso a dependencias Python e imágenes base. Si hay nodos incompatibles,
acordar una etiqueta real y usar `agent { label 'ETIQUETA_ACORDADA' }` en las
copias; no se presupone que exista `linux-podman`.

Comprobar como el usuario del agente: `git --version`, `make --version`,
`uv --version` y `podman info` (o el motor acordado). Comprobar Python 3.12
si se prohíben descargas. Tener herramientas en WSL no las instala en Jenkins.
Se requieren plugins Pipeline/Declarative, Multibranch, Git, Credentials y
GitHub Branch Source, compatibles con el servidor.

| Variable | Comportamiento |
|---|---|
| `CI_CONTAINER` | Motor del agente; predeterminado `podman`. Usar `docker` solo si Plataforma lo proporciona y aprueba. |
| `UV_LOCKED=true` | Falla si `uv.lock` necesita cambios; no regenerar locks en CI. |
| `UV_PYTHON_DOWNLOADS` | Se respeta la política del agente; la plantilla no impone `never`. |
| `CI_DATABASE_URL` | Conexión de pruebas aislada; si no está definida, se usa SQLite en memoria. |
| `DEBUG=false` | Desactiva depuración durante las pruebas. |
| `SECRET_KEY` | Valor público exclusivo de CI; no usarlo para despliegues. |

El Makefile actual de Eventos usa `uv run python -m ruff/pytest` en Linux.
`uv run` prepara el entorno con dependencias de desarrollo; no hace falta una
etapa `make setup`. Sin `uv` se requiere una `.venv` ya preparada. La ejecución
puede escribir `.venv`, cachés y cobertura. Build escribe capas e imágenes en
el motor, usa el Dockerfile y `requirements.txt`, y etiqueta con el SHA que
realmente obtuvo el checkout (en un PR puede ser un commit de combinación).

SQLite permite ensayos unitarios que no requieran PostgreSQL. No demuestra
compatibilidad con PostgreSQL/TimescaleDB. Para una suite que los necesite,
Plataforma/Eventos deben proporcionar una BD de pruebas exclusiva mediante
`CI_DATABASE_URL`; pytest puede crear y eliminar su BD de prueba. Nunca apuntar
a una BD compartida, de desarrollo con datos o de producción. Si la URL contiene
credenciales, inyectarla mediante el mecanismo de secretos acordado y evitar
imprimirla o guardarla en archivos versionados.

`disableConcurrentBuilds()` serializa un job hijo, no otros servicios o ramas.
Usar workspaces propios y bases de prueba independientes entre jobs. El timeout
es de 30 minutos tras asignar el agente y se conservan 15 builds.

## Adaptar a otro servicio

Desde la raíz del repositorio, en Bash/WSL y con la carpeta de destino libre de
trabajo concurrente, este ejemplo escribe un borrador temporal de Problemas:

```bash
sed 's/__SERVICE__/problems/g' platform/templates/Jenkinsfile.template > /tmp/Jenkinsfile.problems
```

Revisarlo, validar el agente/BD y acordar la copia con sus CODEOWNERS antes de
guardarlo como `services/problems/Jenkinsfile`. Para Knowledge reemplazar el
marcador por `knowledge`. Esta entrega solo incorpora la copia de Eventos.

| Servicio | Patrón del filtro | Script Path |
|---|---|---|
| Eventos | `services/events/**` | `services/events/Jenkinsfile` |
| Problemas | `services/problems/**` | `services/problems/Jenkinsfile` |
| Knowledge | `services/knowledge/**` | `services/knowledge/Jenkinsfile` |

## Validación declarativa

Con URL y cuenta autorizada de Jenkins, desde Bash/WSL en la raíz del repo:

```bash
read -r -p 'URL de Jenkins: ' JENKINS_URL
read -r -p 'Usuario de Jenkins: ' JENKINS_USER
curl --fail-with-body --user "$JENKINS_USER" \
  --form 'jenkinsfile=<services/events/Jenkinsfile' \
  "${JENKINS_URL%/}/pipeline-model-converter/validate"
```

Introducir el token API de Jenkins cuando curl solicite contraseña; es distinto
del token GitHub de lectura. Exigir `Jenkinsfile successfully validated.` en el
cuerpo: un HTTP 200 no basta. El linter no prueba las herramientas ni el build.

## Prueba multibranch obligatoria en Eventos

1. Publicar la rama de tarea y abrir PR en borrador a `develop`, con `Refs #86`.
2. Con Plataforma, reutilizar el job `events` o acordar uno de ensayo. Origen:
   `help-chair/help-chair`; credencial de lectura aprobada; Script Path:
   `services/events/Jenkinsfile`; agente capaz de ejecutar las tres etapas.
3. Habilitar el descubrimiento de la rama/PR de prueba. Según la estrategia,
   abrir un PR puede ocultar el job de rama y crear otro de PR. Elegir un job
   hijo y conservarlo durante la matriz; su primer build debe ejecutar CI.
4. Esperar cada ejecución antes del siguiente push. Desde el segundo build,
   con `FORCE_CI=false`, comprobar la matriz de abajo sin mezclar commits.
5. Guardar URLs/logs, SHA construido, archivos del changelog, parámetro y
   resultados de cada etapa, incluida la etiqueta de la imagen. Conservar
   evidencia antes de que actúe la retención de builds.

| Caso | Resultado esperado |
|---|---|
| Primer build del job hijo | Lint, Test y Build ejecutados. |
| Cambio solo en Eventos | Las tres etapas ejecutadas. |
| Cambio solo en esta guía, sin Eventos en el changelog | `CI del servicio` omitida; Checkout ejecutado. |
| Cambios mezclados que incluyen Eventos | Las tres etapas ejecutadas. |
| Sin cambios propios, `FORCE_CI=true` | Las tres etapas ejecutadas. |
| Fallo en lint o test, en ensayo coordinado | Job fallido y etapas posteriores omitidas. |

Usar mejoras reales de comentarios/documentación para los casos por carpeta.
Los fallos intencionados se ensayan sin integrar errores de prueba. No omitir
pruebas ni ocultar fallos para obtener un build verde.

## Dependencias y cierre

La [#85](https://github.com/help-chair/help-chair/issues/85) proporciona servidor
y acceso. El [PR #179](https://github.com/help-chair/help-chair/pull/179), aún
pendiente en el corte del 18-nov-2026, declara token GitHub por aprobar y ausencia
de motor de contenedores. Reconfirmar esas capacidades antes del ensayo.
Sus roles propuestos permiten a `equipo-problems` ejecutar Problems/Knowledge;
para `events` se necesita participación de Eventos o administración autorizada.
No modificar roles ni el servidor desde esta plantilla.

En la base `8974a45`, `events/migrations/0001_timescaledb_extension.py` de Eventos
está vacío y `0002_initial` depende de él. En el ensayo local del 18-nov-2026,
con Python 3.12 y el lock vigente, `make lint` reportó 11 errores de Ruff y
`make test` en SQLite terminó con 4 passed, 18 xfailed y 1 error:
`BadMigrationError: Migration 0001_timescaledb_extension in app events has no Migration class`.
La selección de otra BD no repara una migración vacía. Coordinar la corrección
con Eventos, sin modificar modelos, migraciones o Makefile como parte de #86.
Ese ensayo manual es distinto de la prueba de Jenkins descrita a continuación.

### Evidencia del laboratorio local — 19-nov-2026

Jenkins 2.580.2 con Java 21 aceptó la copia de Eventos mediante el validador real:
`Jenkinsfile successfully validated.`. Un job diagnóstico comprobó Git, Make,
uv, Python 3.12 y una construcción mínima con Podman desde el usuario del agente.
Esa imagen mínima no es la imagen de Eventos.

Se ejecutó un multibranch contra una copia aislada de Eventos servida por HTTP
en loopback, sin publicar commits del producto ni desactivar la protección de
checkout local. En el mismo job hijo se obtuvieron estos resultados:

| Build / SHA de ensayo | Caso | Resultado observado |
|---|---|---|
| 1 / `0c5d4aa` | Primer build, changelog vacío | CI activada; lint falla con 11 errores; Test/Build omitidos por fallo. |
| 2 / `5d909a2` | Solo guía, `FORCE_CI=false` | Checkout correcto; CI omitida por condición; `SUCCESS`. |
| 3 / `ea967b1` | Cambio en Eventos, `FORCE_CI=false` | CI activada; mismo fallo de lint; Test/Build omitidos. |
| 4 / `ea967b1` | Sin cambios nuevos, `FORCE_CI=true` | CI activada manualmente; mismo fallo de lint. |

Los SHA son commits exclusivos del ensayo, no revisiones publicadas en GitHub.
Conservar consolas, URLs locales y resumen de etapas como evidencia para el PR.
Esto valida sintaxis, filtrado y detención ante fallo de lint; no acredita un
lint/test/build completo correcto ni el escaneo/token/roles del servidor de #85.
La ejecución completa sigue bloqueada por los errores del servicio Eventos.

Según [CONTRIBUTING.en.md](../../CONTRIBUTING.en.md), preparar archivos explícitos,
commit y título Conventional Commits, PR a `develop`, aprobación de CODEOWNERS,
checks correctos y conversaciones resueltas. Las plantillas tienen propietario
global y Eventos su equipo: se requiere coordinar ambas áreas. Integración por
squash. Mientras falten pruebas usar `Refs #86`.

Cerrar [#86](https://github.com/help-chair/help-chair/issues/86) solo cuando estén
integradas la plantilla y la guía, exista la copia revisada de Eventos y haya
evidencia multibranch de lint/test/build y del filtro. Entonces usar `Closes #86`
en la entrega completa; el cierre automático depende del merge a la rama
predeterminada y de la configuración del repositorio. Comprobar el estado final.

Referencias: [sintaxis Jenkins](https://www.jenkins.io/doc/book/pipeline/syntax/#when),
[linter](https://www.jenkins.io/doc/book/pipeline/development/#command-line-pipeline-linter),
[primer changelog](https://plugins.jenkins.io/git/#plugin-content-first-build-changelog)
y [variables de uv](https://docs.astral.sh/uv/reference/environment/).
