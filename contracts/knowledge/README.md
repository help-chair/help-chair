# Contrato v0 de KB — #112 / #134

Una sola propuesta OpenAPI para ambas issues. Responsable: Pablo. Contrato v0
propuesto para revisión. No cierra issues ni acredita aprobación de todos los
consumidores, integración de API o conformidad exhaustiva ITIL 4.

## Base y alcance

El contrato de #230 y el modelo de #228 ya están integrados. La
[guía de integración para Frontend](frontend-integration.md) responde a sus tres
preguntas sobre autor, categorías y campos fuera de v0, y coteja los siete
criterios de #112 sin presentar decisiones pendientes como acuerdos.

- Modelo/fixture: PR #228, commit `4f8573d442de3c01a4f866d5468f3f4ac6e2d4ec`,
  todavía abierto al elaborar el borrador. No duplica ni modifica su esquema.
- Archivo: `contracts/knowledge/openapi.yaml`; esta carpeta contiene
  también los verificadores en `contracts/knowledge/scripts/`.
- OpenAPI 3.0.3, versión documental 0.1.0. El v1 de la ruta no afirma que ya exista
  un contrato de servicio v1 congelado o una API operativa.
- Las cinco operaciones de negocio son **previstas**; las dos de salud existen
  en código. `x-implementation-status` distingue ambos estados.
- No se implementan CRUD, búsqueda PostgreSQL, JWT, permisos, transiciones o motor
  de matching. Uso/feedback/métricas quedan en sus fases posteriores.

## Propuestas que necesitan revisión

| Tema | Propuesta del borrador | Pendiente con |
|---|---|---|
| Rutas | Origen local 8006; prefijo `/api/knowledge/v1`; salud sin ese prefijo | Frontend / Plataforma |
| Operaciones | GET/POST artículos; GET/PATCH detalle; GET soluciones | Eventos, Incidencias, Problemas, Frontend |
| Búsqueda | `q` sobre título/contenido; categoría local; candidatos publicados | Eventos / Frontend |
| Paginación | page desde 1; page_size 20, máximo 100; count/next/previous/results | Consumidores |
| Errores | codigo/detalle/campos; 400/401/403/404/409/503 según operación | Consumidores |
| Edición | Alta en borrador, PATCH solo borrador, autor/estado/fechas no editables | Equipo de KB |
| Identidad | JWT Accesos, validación de sub/empresa/emisor/expiración; permisos KB sin inventar | Accesos |
| Soluciones | Candidatos accesibles; selección/aplicabilidad, timeout y reintentos pendientes | Eventos |

El contrato de Problemas v0.2.0, actualizado por el [PR #223 integrado](https://github.com/help-chair/help-chair/pull/223),
usa origen `http://localhost:8005` y rutas completas `/api/problems/v1/...`.
Referencia fijada: [OpenAPI de Problemas en el merge de #223](https://github.com/help-chair/help-chair/blob/fa8d58a5c256e1095ad030f413ac901c19d56d7c/contracts/problems/openapi.yaml).
Conserva page/page_size y codigo/detalle/campos; Eventos usa
`/api/events/v1`, limit/offset y code/detail/fields. Esas diferencias no son una
convención común aprobada. El contrato de Accesos v0 declara HS256; RS256/JWKS
está previsto después. No se incorpora una implementación de ninguno.

## Correspondencia con el modelo

UUID de artículo → `id: string/uuid`, estable y compatible con la referencia textual
de Problemas de hasta 64 caracteres. `autor_id` es UUID externo de Accesos, sin FK;
la API futura lo deriva de `sub`, nunca del cuerpo o del usuario staff local.
Los DTO de creación/edición no admiten campos extra, identidad, empresa o fechas.
El código de categoría es local, dinámico, máximo 50; el título admite 200.
Contenido Markdown es canónico; no se duplica en arrays de pasos/síntomas.

Estado (`borrador/publicado/archivado`) y audiencia (`empresa/soporte`) son distintos.
`empresa` exige autenticación del stack, no publicación en internet. El borrador
puede estar incompleto; un publicado requiere categoría, autor, fecha y texto no
blanco; el archivo conserva identidad y última publicación. Los esquemas de lectura
distinguen esos estados. Orden cronológico y categoría activa requieren además
reglas de modelo/servicio; un JSON Schema no comprueba la BD ni la identidad.

Los cuatro ejemplos de lectura reproducen exactamente la fixture canónica, que
contiene datos de dominio sintéticos, no credenciales. Creado/Editado son
proyecciones de API sobre esos datos para mostrar autor y fechas del servidor.
Los mocks frontend `KB-028`, `publico/agentes`, resumen, pasos, métricas y
`error_conocido_id` no se convierten automáticamente en campos del backend.
El vínculo autoritativo permanece en Problemas; varios errores pueden referenciar
el mismo artículo, sin FK ni relación inversa maestra.

## Trazabilidad de #112, #134 y #137

Esta matriz distingue evidencia local ya ejecutada de acuerdos pendientes; no
marca criterios de las issues como cerrados ni sustituye la revisión humana.

| Criterio | Entrega/evidencia disponible | Qué falta |
|---|---|---|
| #112/#134: OpenAPI de KB y operaciones | YAML integrado por PR #230; cinco operaciones de negocio previstas y dos de salud | Acuerdos abiertos no se resuelven solo por integración |
| #112/#134: DTO consistente con el modelo | Lectura/alta/PATCH contrastados con #228 integrado; cuatro artículos de fixture fijados a 4f8573d | Confirmación de consumidores |
| #112/#134: entradas, respuestas, errores y ejemplos válidos | 41 ejemplos y 37 negativos aprobados; OpenAPI válido; 16 casos Prism | No prueba API real, permisos, búsqueda o reglas de BD |
| #112: audiencia, autenticación y referencias por ID | Propuestas explícitas; UUID cabe en articulo_kb_id de texto de hasta 64 caracteres | Acuerdos de Accesos y consumidores; no hay FK externa |
| #112: revisión registrada y distinción previsto/implementado | Aprobación de Leon2411, observación neutral de Frontend, matriz A1–A9; x-implementation-status | Respuestas/acuerdos restantes y revisión de las aclaraciones |
| #137: revisión de ambos contratos | Ambos contratos integrados; operaciones de KB aún previstas | OK de Eventos, Incidencias y Frontend sobre ambos contratos; comentarios atendidos y flujo de integración autorizado |

La [matriz A1–A9 del PR #230](https://github.com/help-chair/help-chair/pull/230#issuecomment-7084100013)
concentra las preguntas; evitar solicitudes duplicadas. Al corte del 24 de noviembre
existen aprobación de Leon2411 y una [revisión neutral de Frontend](https://github.com/help-chair/help-chair/pull/230#issuecomment-7089155841)
con tres preguntas. La [guía de integración](frontend-integration.md) prepara su
respuesta técnica, sin atribuirle aprobación de todos los acuerdos o equipos.
La [aprobación de Pablo en #182](https://github.com/help-chair/help-chair/pull/182#pullrequestreview-5967452203)
corresponde al commit 67b2dee del contrato anterior de Problemas. No acredita por
sí sola el OK de los tres equipos exigidos por #137, la revisión del cambio de
prefijo de #223 ni la aprobación del contrato de KB.

### Checklist para revisión de compatibilidad de ambos contratos

Cada equipo debe registrar el contrato/commit revisado y el resultado, indicando
un cambio concreto si lo requiere. Estos puntos permanecen abiertos hasta su OK:

- [ ] Eventos, Incidencias y Frontend verifican las URLs completas: Problemas
  `/api/problems/v1/...` vigente y KB `/api/knowledge/v1/...` propuesto; sin duplicar
  prefijo en servers/paths y sin imponer que toda API tenga idénticas convenciones.
- [ ] Problemas/consumidores aceptan el UUID canónico de KB como referencia textual
  externa de hasta 64 caracteres. Los IDs internos int64 de Problemas no cambian;
  los ejemplos históricos KB-128 no crean un alias implementado en KB.
- [ ] Los estados de Problemas y de artículo conservan sus dominios separados;
  audiencia empresa/soporte no es un estado. Confirmar campos de lectura,
  escritura, nulabilidad de borrador y autor/fechas gestionados por servidor.
- [ ] Los clientes interpretan páginas, filtros, vacío y errores: page/page_size
  en Problemas/KB propuesto frente a limit/offset de Eventos; distinguir 404,
  503 y timeout de una búsqueda válida sin resultados.
- [ ] Accesos y consumidores acuerdan permisos y contexto delegado, sin ampliar
  la audiencia del usuario final por llamar mediante un servicio.
- [ ] Eventos confirma selección/aplicabilidad antes de auto-responder: los
  candidatos no implican dificultad fácil ni solución confirmada. Versión,
  departamento y otros metadatos ausentes requieren un acuerdo separado.
- [ ] Frontend adapta mocks/DTO a UUID, Markdown y categoría local; no confunde
  ejemplos y contadores en memoria con integración o métricas reales.

Los ensayos operativos del runtime tienen evidencia separada en los PR #229 y
#231; no se atribuyen a este contrato ni sustituyen la aprobación de consumidores.

## Consulta de soluciones y seguridad

La búsqueda textual devuelve candidatos, no una solución confirmada ni una
clasificación de dificultad. El modelo no contiene servicio, dificultad,
aplicabilidad estructurada, versión formal o departamento. No se inventan esos
metadatos ni filtros. Eventos adapta id/titulo/autor_id a sus referencias; deberá
aceptar omitir versión/departamento o acordar otra contribución separada.
La categoría KB no equivale a la clasificación de Eventos.

Usuario final: publicados de audiencia empresa. Soporte autorizado: alcance
editorial por acordar. Una identidad de servicio no amplía la audiencia del usuario
final. Debe acordarse cómo se delega ese contexto; el borrador no declara el flujo
resuelto. Recurso inexistente/no accesible: 404 propuesto. Lista vacía se diferencia
de 503/timeout y no activa automáticamente auto-respuesta.

No hay tokens/JWT de muestra ni valores de configuración secretos. El contrato y
sus verificadores no requieren SECRET_KEY, DATABASE_URL, `.env`, Django ni una BD.
No leen ni vuelcan el entorno del servicio. Configuración de #111: entorno real
del proceso, secretos fuera de Git, sin defaults secretos ni `.env` automático.

## Verificación reproducible

Usar un entorno externo ya preparado con Python 3.12, openapi-spec-validator 0.9.0,
openapi-schema-validator 0.9.0 (dependencia del anterior), PyYAML 6.0.3 y git.
No regenerar el lock del servicio. Desde esta carpeta:

```bash
python -m openapi_spec_validator openapi.yaml
python scripts/validate_contract.py --repo ../..
```

Si está preparado aparte detect-secrets 1.5.0, `python scripts/scan_secrets.py`
revisa únicamente los artefactos de esta carpeta, sin verificación por red y sin
imprimir valores, hashes o líneas detectadas. No genera baseline ni excluye
plugins. Una alerta se revisa localmente antes de copiar/publicar; un resultado
limpio no garantiza ausencia absoluta de secretos ni sustituye revisar commits.

No todos los acuerdos de comportamiento son expresables en OpenAPI 3.0: Prism
no demuestra rechazo de parámetros query desconocidos, categoría activa,
audiencia efectiva, orden cronológico, ranking o transiciones. Esos casos
necesitarán pruebas de la API cuando se implemente; no se atribuyen al mock.

El verificador valida estructura, referencias locales, ejemplos de cada operación,
formatos, variantes de lectura, payloads de escritura, negativos y correspondencia
de los cuatro artículos de la fixture **fijada al commit**, sin importar Django.
Los fallos no imprimen instancias, entorno ni valores internos. No comprueba reglas
de BD, autenticación real, filtros, ranking ni concurrencia del runtime.

Para Prism, preparar su CLI fuera del repo (versión verificada 5.16.0), y pasar su
entry point ya instalado a `node scripts/mock_smoke.mjs`. El script liga loopback
en puerto libre, inicia y detiene solo su proceso y suprime sus logs. Genera un
bearer opaco efímero en memoria para satisfacer el mock, que **no es un JWT**,
no se imprime/persiste y no se reenvía a servicios reales. Comprueba rutas,
ejemplos, vacío, errores y rechazo estructural. Prism selecciona el 400 descrito
para entradas inválidas; su informe de validación no demuestra que el runtime
implemente el envelope de errores de KB. Forzar 503 mediante
Prefer prueba ejemplos del mock, no una caída real de KB. Un mock no persiste POST
ni demuestra autorización; sus ejemplos se seleccionan explícitamente.

## Entrega y revisión posterior

1. La contribución contiene solo YAML, README y estos scripts; no modifica
   servicios ni añade recursos temporales o evidencia privada al repositorio.
2. La rama de contratos parte de develop sin heredar los modelos del PR #228 ni
   el runtime del PR #229. Los acuerdos de modelo y ejecución se coordinan con
   esas propuestas; no se copian sus implementaciones a este PR.
3. Repetir validación contra el modelo que finalmente se integre y contrastar
   salud con el código de #111. No duplicar fixture ni modificar migraciones.
4. El PR #229 de #111 propone separar la exportación de runtime: `make openapi`
   requiere OPENAPI_OUTPUT explícito fuera de contracts/ y rechaza destinos dentro de contracts/.
   No utilizar una exportación de las rutas actuales como sustituto de este
   diseño de negocio previsto. Este contrato se valida con sus propios scripts.
5. Revisiones: CODEOWNER Knowledge (otro autor), Eventos, Incidencias, Problemas,
   Frontend; Accesos/Plataforma para los acuerdos descritos. Registrar OK reales
   en el PR cuando su publicación sea autorizada; un borrador no sustituye ese OK.
6. Mantener Refs #112/#134 hasta cumplir sus criterios; no cerrar duplicadas ni
   atribuir acuerdos, API implementada o integración a pruebas con mocks.

Pablo asume pruebas, documentación y evidencia de #111/#112. Este PR no publica
imágenes ni despliegues y no declara operaciones de negocio implementadas.

## Evidencia del borrador — 22 de noviembre de 2026

Verificación del borrador y de su copia local: Python 3.12.16, Node 24.22.0, Prism 5.16.0;
validadores OpenAPI 0.9.0, PyYAML 6.0.3, Ruff 0.15.7, detect-secrets 1.5.0.
Dependencias preparadas fuera del checkout, sin tocar locks del proyecto.

```text
CLI openapi_spec_validator: OK
PASS OpenAPI 3.0.3; operations=7; examples=41; negative_cases=37; pinned_fixture_articles=4
PASS Prism loopback smoke: checks=16; no API/JWT/DB integration claimed
Ruff: All checks passed / format check correcto
PASS artifact scan: files=5; findings=0
```

Dos revisiones estáticas del borrador corrigieron una descripción YAML y la
comprobación de límites de paginación; la última no detectó bloqueantes.
No equivalen a aprobación de CODEOWNERS ni de los consumidores.
Prism se detuvo al terminar; no se arrancaron APIs ni BD. No se ejecutó la suite
Django de #111 ni la de modelos del PR #228 en esta actividad contractual.
El contrato está integrado en contracts/knowledge y #134 está completada. #112
sigue abierta: hay aprobación registrada en #230 y respuesta neutral de Frontend,
pero quedan acuerdos y revisión de las aclaraciones de integración pendientes.
