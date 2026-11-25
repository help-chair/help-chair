# Integración de Frontend con KB v0 — aclaraciones de #112

Corte: 24 de noviembre de 2026, sobre develop `0451e4ac`.
Este documento responde técnicamente a las tres preguntas de la
[revisión neutral de Frontend en #230](https://github.com/help-chair/help-chair/pull/230#issuecomment-7089155841).
No es una respuesta publicada en ese hilo ni un acuerdo aprobado por consumidores.
No añade campos, rutas, permisos o implementación de negocio.

El contrato y los modelos están integrados por #230 y #228 respectivamente.
Eso no convierte las rutas de artículos/búsqueda/soluciones en operaciones
implementadas: la configuración de URLs de KB en este corte solo registra salud,
admin, esquema y documentación. Una vista contra mocks no prueba integración real.

## 1. Autor: UUID de referencia, no nombre incluido por KB

**Respuesta vigente:** el DTO devuelve `autor_id`, UUID externo nullable en
borradores. No devuelve `autor`, `autor_nombre` ni otro dato de perfil. El alta
prevista toma el sujeto de autenticación validado; el cliente no envía autor.
La fixture admite borradores sin autor y usa autores sintéticos, que no garantizan
que exista una cuenta correspondiente en Accesos. Un publicado requiere autor.

Accesos sí documenta `GET /api/access/v1/usuarios/{id}` y una respuesta `Usuario`
con `nombre`. Hay ruta y vista para esa consulta, pero `UserDetailView` exige
autenticación y **`usuarios:administrar`**. No se debe presentar como un mecanismo
de resolución disponible para todos los lectores de KB ni conceder permisos de
administración solo para mostrar un nombre. `/me` tampoco resuelve otro autor.
Esto es cotejo estático, no una nueva prueba de Accesos o sus permisos efectivos.

Comportamiento de presentación recomendado, pendiente de acuerdo con Frontend:

- Conservar el UUID como identidad canónica; no sustituirlo por un nombre o alias.
- Si el principal ya está autorizado a consultar Accesos, podrá usar su contrato
  y conservar únicamente el nombre necesario para la vista, dentro del stack y
  contexto de ese usuario. No consultar ni copiar su BD ni exponer correo/rol.
- Si falta autor o la consulta no está autorizada, no existe o falla, la lectura
  del artículo no debe depender del nombre: mostrar una etiqueta como «Sin autor»
  para null o «Autor no disponible» para referencia sin resolución. No inventar
  personas ni presentar el UUID como si fuera un nombre.
- No incluir una credencial privilegiada en Frontend ni usar un servicio para
  saltarse la audiencia o los permisos del usuario final.

**Propuesta separada P-AUTOR-01, no implementada ni aprobada:** acordar con Accesos
una proyección mínima de identidad o un enriquecimiento autorizado, su audiencia,
minimización de datos, indisponibilidad y actualización. Si se elige que KB incluya
nombre, requiere una revisión versionada del contrato y su origen; no una nueva
columna de nombre duplicada por este documento. Mientras tanto el DTO v0 no cambia.

## 2. Categorías: código local dinámico, sin catálogo REST de KB en v0

**Respuesta vigente:** no existe operación de catálogo en el OpenAPI de KB ni
ruta REST de categorías en su configuración actual. `categoria` transporta el
código local de `Categoria`, no un enum cerrado ni un ID del catálogo de Eventos.
El modelo guarda código (máximo 50), nombre y activa; la FK de artículo es local
y nullable en borrador. La existencia de modelo/admin no equivale a un catálogo API.

La fixture canónica contiene `red` → «Red (demostración)» y `software` →
«Software (demostración)». Son datos sintéticos de ensayo, **no** un catálogo
exhaustivo o obligatorio de las empresas. No copiar la lista fija del mock como
fuente autorizada de códigos ni deducir una etiqueta oficial desde un slug.

Recomendación actual para mocks/presentación, sin modificar Frontend en esta entrega:

- Tipar el código como string; admitir null en borrador. Un código desconocido
  para la vista no debe romper el artículo: mostrar el código recibido como
  fallback explícito, sin afirmar que es el nombre oficial de la categoría.
- Si no hay catálogo autorizado, no ofrecer un selector supuestamente completo
  ni fabricar opciones. La edición que lo necesite queda sin selector operativo
  hasta acordar su fuente; no confundir esto con un bloqueo de la lectura del DTO.
- No enviar nombres visibles en el campo `categoria` ni crear códigos al vuelo.
  La API prevista deberá validar existencia al escribir; un filtro por código
  desconocido produce lista vacía según el contrato, no crea una categoría.
- En ensayos solo se usan códigos de la fixture o datos curados explícitos del
  entorno de prueba; no convertirlos en una configuración de producción.

**Propuesta separada P-CATEGORIAS-01, no implementada ni aprobada:** preparar una
ampliación versionada de solo lectura para obtener código, nombre y activa.
Debe acordar ruta, autorización/audiencia, tratamiento de inactivas o categorías
ya referenciadas, orden/paginación y errores. No es un CRUD de categorías; el
contrato v0 actual no incluye esa ruta. No se promete una llamada REST existente
ni se consulta la base de otro servicio para suplirla.

## 3. Campos editoriales, uso y valoraciones fuera del DTO v0

**Confirmación del alcance técnico vigente:** no están en el DTO `resumen`,
`sintomas`, `pasos`, `si_no_funciona`, métricas o valoraciones. El contenido
canónico es Markdown. Sus secciones pueden describir pasos/síntomas, pero no se
garantizan arrays ni se extraen por heurísticas como otra fuente editable.
Registro de uso y valoración corresponden a fase III; no se crean ahora sus
endpoints o contadores. Un resumen derivado para presentación, si se acuerda,
no se debe enviar a KB como si fuera un campo persistente.

| Mock provisional | DTO/decisión vigente | Adaptación propuesta del consumidor |
|---|---|---|
| Alias `KB-028` | `id` UUID canónico | Usar UUID en rutas/referencias; no asumir alias implementado |
| `autor` como nombre | `autor_id` externo; null posible en borrador | Aplicar el límite de resolución de la sección 1 |
| Categoría enum fijo | Código local dinámico | String/null; fuente de etiquetas pendiente, sección 2 |
| `publico/agentes` | `empresa/soporte` | Adoptar enum; empresa exige autenticación, no internet |
| `resumen`, `sintomas`, `pasos`, `si_no_funciona` | Ausentes; `contenido` Markdown canónico | Adaptar vista, sin enviar propiedades extra ni duplicar cuerpo |
| `consultas`, `votos_utiles`, `votos_no_utiles`, valoración | Ausentes del v0 | No mostrar contadores del mock como métricas reales |
| `error_conocido_id` inverso | Vínculo autoritativo en Problemas: `articulo_kb_id` textual ≤64 | No añadir relación inversa maestra o FK externa |
| Estado/fechas no tipados | `estado`, `creado_en`, `actualizado_en`, `publicado_en`, `archivado_en` | Respetar nulabilidad/solo lectura; no mapear estado a audiencia |

Estas respuestas aclaran el contrato actual, no aprueban por Frontend la adaptación
ni cierran A1–A9. Las soluciones para Eventos siguen siendo candidatos accesibles;
no se incorporan dificultad, versión, departamento o aplicabilidad estructurada.

## Cotejo de los siete criterios de #112

| Criterio | Evidencia técnica disponible | Límite o pendiente externo |
|---|---|---|
| 1. YAML versionado y válido | OpenAPI integrado en #230; validación histórica 41 ejemplos/37 negativos | Prosa de esta aclaración no cambia ni revalida el YAML |
| 2. Esquemas/IDs/estados coherentes | Modelo y fixture de #228; DTO UUID, categoría local, estado/audiencia separados | No equivale a API implementada ni a OK de todos los consumidores |
| 3. Entradas/respuestas/errores/ejemplos | Cinco operaciones previstas, variantes de lectura/escritura y errores documentados | Nuevos campos/catálogos requieren ampliación acordada |
| 4. Visibilidad/autenticación | Propuestas y pendientes de Accesos explícitos en YAML/README | Permisos editoriales y delegación aún por acordar |
| 5. Referencias y comportamiento con consumidores | IDs externos, vacío/error y candidatos descritos; preguntas A1–A9; aclaraciones presentes | Falta confirmar acuerdos concretos con Problemas, Eventos e Incidencias |
| 6. Revisión registrada en PR | Aprobación de Leon2411 y comentario neutral de Frontend en #230 | No atribuir el comentario neutral a todos los equipos ni cerrar sus tres preguntas sin su respuesta |
| 7. Previsto frente a implementado | x-implementation-status, límites de mocks y rutas actuales documentados | No se implementa CRUD/JWT/búsqueda por esta contribución |

La corrida del 22 de noviembre acredita 41 ejemplos, 37 negativos, cuatro
proyecciones canónicas y 16 casos Prism sobre los artefactos entonces verificados.
No son ejecuciones del 24 ni prueba de Jenkins. Esta contribución documental no
repite esas pruebas si los blobs de YAML/verificadores permanecen idénticos.

## Fuentes cotejadas

Fuentes de código fijadas al [corte develop 0451e4ac](https://github.com/help-chair/help-chair/tree/0451e4ac01d0ad4069a5ba4abbe13a9a2abfc9b9):

- [OpenAPI de KB](openapi.yaml), [README](README.md) y sus verificadores.
- [Modelos KB](../../services/knowledge/articles/models.py),
  [fixture canónica](../../services/knowledge/articles/fixtures/kb_demo.json) y
  [rutas del servicio](../../services/knowledge/config/urls.py).
- [Contrato de Accesos](../access/openapi.yaml): getUser y esquema Usuario;
  [rutas](../../services/access/core/auth_urls.py) y
  [UserDetailView](../../services/access/core/users.py), que exige usuarios:administrar.
- [Contrato de Problemas](../problems/openapi.yaml): referencia externa textual.
- [Tipos provisionales de Frontend](../../frontend/src/features/knowledge/types.ts).

No se han probado de nuevo esos servicios, cambiado sus permisos o copiado datos
de usuarios. #112 permanece abierta; #134 ya está completed. Cualquier publicación,
respuesta en PR o cierre requiere su autorización correspondiente.
