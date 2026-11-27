# Reglas de destino de Eventos / Event routing rules

*Español primero, English below.*

> Relacionado / Related: [`ARCHITECTURE.md`](ARCHITECTURE.md) (§6) · [`ITIL-MAPPING.md`](ITIL-MAPPING.md) · [`test_rules.py`](../services/events/tests/test_rules.py)

---

## Español

### 1. Propósito y alcance

- El motor de **Eventos** recibe un evento y decide a dónde va.
- Práctica ITIL v4: **Monitoring and Event Management** (Gestión de Eventos).
- Estas reglas son la **especificación** del servicio (issue #67).
- Se verifican con pruebas **pytest parametrizadas** en `services/events/tests/test_rules.py` antes de implementar el motor (**TDD**).
- Las pruebas de comportamiento aún no implementado quedan marcadas como `xfail`.
- Servicios existentes: Accesos, Eventos, Peticiones, Incidencias, Problemas y Base de Conocimiento (KB).

### 2. Reglas de destino

| # | Condición | Tipo | Destino | Descripción |
|---|---|---|---|---|
| 1 | Evento de sistema | Informativo | Solo registro | Un evento informativo no necesita gestión, solo queda como bitácora y se cierra solo, sin intervención. |
| 2 | Lo dispara un usuario y hay solución en la KB | Informativo | El autor de dicha solución | Es autoservicio con la base de conocimiento; se le entrega al usuario la solución ya redactada. Si la encuesta dice "no resolvió", el evento se redirige al autor de la solución. |
| 3 | Advertencia bajo el umbral de recurrencia | Advertencia | Eventos | Advertencia aislada o poco frecuente: se registra y suma a un contador. Si supera el umbral (N veces en T días), se reevalúa y pasa a Problemas (regla 7). |
| 4 | Seguridad o credenciales no informativas | Advertencia (eventos de seguridad de Accesos marcados como excepción conservan `EXCEPTION`) | Accesos / Seguridad | Se verifica directamente con Accesos, que valida la solicitud y toma la acción de seguridad pertinente. |
| 5 | Solicitud estándar del catálogo | Informativo | Peticiones | Requisito de un departamento ya contemplado en el catálogo de servicios. |
| 6 | Falla, degradación o interrupción | Excepción | Incidencias | Restauración del servicio ante una falla puntual, sin buscar todavía la causa de fondo. |
| 7 | Patrón repetido | Excepción | Problemas | Se registra cuántas veces se repitió el patrón para investigar la causa raíz y documentar posibles soluciones o un **Error conocido**. |
| 8 | Requiere modificar configuración o infraestructura | Informativo | Peticiones | Si hace falta cambiar equipo, configuración o instrumentación, Peticiones gestiona el cambio, ya que el MVP absorbe Change Enablement. |
| 9 | Ninguna de las anteriores coincide | Excepción | Incidencias | El evento no pudo encontrar una relación; pasa a Incidencias para que se revise y clasifique (**triage manual**). |

- La columna **Tipo** es la clasificación ITIL que **la regla asigna** al evento (Informativo, Advertencia o Excepción); no es una condición de entrada y puede diferir del tipo con el que llegó. Ejemplos: un evento de seguridad que llega como Excepción sale como Advertencia (regla 4); una advertencia que alcanza el umbral sale como Excepción (regla 7).
- Excepción específica de R4: los eventos contractuales `access.cuenta.bloqueada` y `access.password.cambiada` con `forzado=true` conservan `EXCEPTION` al enrutarse a Accesos. El resto de los eventos de seguridad mantiene la clasificación definida por R4. La detección literal de logins forzados o permisos indebidos queda pendiente de que Accesos los publique en el contrato.
- Los eventos informativos de seguridad (como los logins exitosos y los fallidos bajo el umbral) no pasan por R4, para conservar su clasificación informativa.
- Las reglas 1, 2 y 3 se resuelven dentro de Eventos o con la KB; las demás enrutan a otro servicio.

### 3. Orden de evaluación

> Propuesta, por confirmar con el equipo.

**La primera regla que coincide gana.** Orden: `4 → 2 → 7 → 8 → 5 → 6 → 3 → 1 → 9`.

| Posición | Regla | Justificación |
|---|---|---|
| 1 | 4 | La seguridad no informativa siempre va primero, aunque haya solución en la KB o el evento se repita. |
| 2 | 2 | El autoservicio con KB va antes de abrir trabajo en otro servicio. |
| 3 | 7 | Los patrones repetidos van antes que fallas o advertencias individuales. |
| 4 | 8 | Un cambio de infraestructura es más específico que una solicitud estándar. |
| 5 | 5 | Solicitud explícita del catálogo. |
| 6 | 6 | Falla puntual, no repetida: restaurar el servicio. |
| 7 | 3 | Advertencia bajo el umbral: solo suma al contador. |
| 8 | 1 | Informativo de sistema sin acción: solo registro. |
| 9 | 9 | Red de seguridad; siempre al final. |

### 4. Entradas y salidas

**Entrada:** campos del evento.

| Campo | Tipo de dato | Valores |
|---|---|---|
| `origen` | texto | `sistema`, `usuario` |
| `tipo` | texto | `informativo`, `advertencia`, `excepcion` (tipo con el que llega el evento) |
| `requiere_accion` | bool | `true`, `false` |
| `categoria` | texto o vacío | `seguridad`, `solicitud_catalogo`, `falla`, `cambio`; vacío si no aplica |
| `autor_solucion_kb` | texto o vacío | autor del artículo de la KB que resuelve el evento |
| `repeticiones` | entero | veces que se repitió el patrón dentro de la ventana de T días |
| `umbral` | entero | N |

**Salida:** `Decision(regla, destino, tipo)`.

| Regla | Condición en campos | `destino` | `tipo` asignado |
|---|---|---|---|
| 1 | `origen = sistema`, `tipo = informativo`, `requiere_accion = false` | `registro` | `informativo` |
| 2 | `origen = usuario`, `autor_solucion_kb` no vacío | `autor_solucion` | `informativo` |
| 3 | `tipo = advertencia`, `repeticiones < umbral` | `eventos` | `advertencia` |
| 4 | `categoria = seguridad`, `tipo != informativo` | `accesos` | `advertencia` (salvo la excepción contractual de seguridad de Accesos) |
| 5 | `categoria = solicitud_catalogo` | `peticiones` | `informativo` |
| 6 | `categoria = falla` | `incidencias` | `excepcion` |
| 7 | `repeticiones >= umbral` | `problemas` | `excepcion` |
| 8 | `categoria = cambio` | `peticiones` | `informativo` |
| 9 | ninguna de las anteriores | `incidencias` | `excepcion` |

- Las condiciones se evalúan en el orden de la sección 3, no en orden numérico.
- `tipo` de la salida es la clasificación asignada por la regla (sección 2); el `tipo` de la entrada solo participa en las reglas 1 y 3.
- "Superar el umbral" se interpreta como `repeticiones >= umbral`.

### 5. Casos de borde y pruebas

| Caso | Regla esperada | Tipo asignado |
|---|---|---|
| Advertencia con `repeticiones = umbral - 1` | 3 | Advertencia |
| Advertencia con `repeticiones = umbral` | 7 | Excepción (reclasificada) |
| Falla repetida (`repeticiones >= umbral`) | 7 (no 6) | Excepción |
| Seguridad con solución en KB o repetida | 4 | Advertencia |
| Falla de usuario con solución en KB | 2 | Informativo |
| Informativo de usuario sin KB | 9 | Excepción |
| Evento de sistema informativo con `requiere_accion = true` | 9 | Excepción |
| Evento sin coincidencia | 9 | Excepción |

**Correr las pruebas:**

```bash
cd services/events
make test
```

- Las pruebas pendientes aparecen como `xfail` con su motivo.
- Dos pruebas guardia (sin `xfail`) verifican que las 9 reglas tengan al menos un caso y que el tipo asignado de cada una coincida con la tabla de la sección 2.

### 6. Supuestos y decisiones abiertas

- El orden de evaluación (sección 3) está por confirmar con el equipo.
- La regla 7 se evalúa solo por `repeticiones >= umbral`, no por "causa raíz desconocida", para no mandar toda falla nueva a Problemas.
- La regla 7 no distingue el `tipo` de entrada: un informativo repetido también llegaría a Problemas y se reclasificaría como Excepción. Por confirmar si se excluye.
- El `tipo` de salida lo asigna la regla; el `tipo` de entrada solo se usa en las reglas 1 y 3.
- La encuesta de la regla 2 no se modela en el motor: el destino es `autor_solucion` tanto al entregar la solución como al responder "no resolvió".
- El canal de la alerta al superar el umbral (regla 3) no está definido.
- El motor recibe `repeticiones` ya calculadas; N y T son parámetros externos.
- La KB debe guardar el autor de cada artículo para llenar `autor_solucion_kb`.

### 7. Referencias

- [`ARCHITECTURE.md`](ARCHITECTURE.md): sección 6, flujo de Eventos.
- [`ITIL-MAPPING.md`](ITIL-MAPPING.md): mapeo de servicios a prácticas ITIL v4.
- [`test_rules.py`](../services/events/tests/test_rules.py): pruebas parametrizadas de las reglas.

---

## English

### 1. Purpose and scope

- The **Events** engine receives an event and decides where it goes.
- ITIL v4 practice: **Monitoring and Event Management**.
- These rules are the service **specification** (issue #67).
- They are verified with **parametrized pytest** tests in `services/events/tests/test_rules.py` before the engine is implemented (**TDD**).
- Tests for behavior not yet implemented are marked `xfail`.
- Existing services: Access, Events, Requests, Incidents, Problems and Knowledge Base (KB).

### 2. Routing rules

| # | Condition | Type | Destination | Description |
|---|---|---|---|---|
| 1 | System event | Informational | Log only | An informational event needs no management; it is kept as a log entry and closes itself, with no intervention. |
| 2 | Triggered by a user and a KB solution exists | Informational | The author of that solution | Self-service through the knowledge base; the user receives the already written solution. If the survey says "not resolved", the event is redirected to the solution's author. |
| 3 | Warning below the recurrence threshold | Warning | Events | Isolated or infrequent warning: it is logged and added to a counter. If it exceeds the threshold (N times in T days), it is re-evaluated and moves to Problems (rule 7). |
| 4 | Non-informational security or credentials | Warning (contractual Access security exceptions retain `EXCEPTION`) | Access / Security | Verified directly with Access, which validates the request and takes the appropriate security action. |
| 5 | Standard catalog request | Informational | Requests | A department requirement already covered by the service catalog. |
| 6 | Failure, degradation or outage | Exception | Incidents | Service restoration after a one-off failure, without looking for the underlying cause yet. |
| 7 | Repeated pattern | Exception | Problems | The number of repetitions is recorded to investigate the root cause and document possible solutions or a **Known Error**. |
| 8 | Requires a configuration or infrastructure change | Informational | Requests | If equipment, configuration or instrumentation must change, Requests manages the change, since the MVP absorbs Change Enablement. |
| 9 | None of the above matches | Exception | Incidents | The event could not be matched; it goes to Incidents for review and classification (**manual triage**). |

- The **Type** column is the ITIL classification that **the rule assigns** to the event (Informational, Warning or Exception); it is not an input condition and may differ from the type the event arrived with. Examples: a security event arriving as Exception leaves as Warning (rule 4); a warning that reaches the threshold leaves as Exception (rule 7).
- R4 exception: contractual `access.cuenta.bloqueada` and `access.password.cambiada` messages with `forzado=true` retain `EXCEPTION` when routed to Access. Other security events keep R4's existing classification. Literal forced-login and improper-permission detection waits for Access to publish those event types in its contract.
- Informational security events (such as successful logins and failed logins below the threshold) do not pass through R4, preserving their informational classification.
- Rules 1, 2 and 3 are resolved inside Events or with the KB; the others route to another service.

### 3. Evaluation order

> Proposal, to be confirmed with the team.

**The first matching rule wins.** Order: `4 → 2 → 7 → 8 → 5 → 6 → 3 → 1 → 9`.

| Position | Rule | Rationale |
|---|---|---|
| 1 | 4 | Non-informational security always comes first, even if a KB solution exists or the event repeats. |
| 2 | 2 | KB self-service comes before opening work in another service. |
| 3 | 7 | Repeated patterns come before individual failures or warnings. |
| 4 | 8 | An infrastructure change is more specific than a standard request. |
| 5 | 5 | Explicit catalog request. |
| 6 | 6 | One-off, non-repeated failure: restore the service. |
| 7 | 3 | Warning below the threshold: only adds to the counter. |
| 8 | 1 | System informational event with no action: log only. |
| 9 | 9 | Safety net; always last. |

### 4. Inputs and outputs

**Input:** event fields.

| Field | Data type | Values |
|---|---|---|
| `origen` | text | `sistema`, `usuario` |
| `tipo` | text | `informativo`, `advertencia`, `excepcion` (type the event arrives with) |
| `requiere_accion` | bool | `true`, `false` |
| `categoria` | text or empty | `seguridad`, `solicitud_catalogo`, `falla`, `cambio`; empty if none applies |
| `autor_solucion_kb` | text or empty | author of the KB article that resolves the event |
| `repeticiones` | integer | times the pattern repeated within the T-day window |
| `umbral` | integer | N |

**Output:** `Decision(regla, destino, tipo)`.

| Rule | Field condition | `destino` | Assigned `tipo` |
|---|---|---|---|
| 1 | `origen = sistema`, `tipo = informativo`, `requiere_accion = false` | `registro` | `informativo` |
| 2 | `origen = usuario`, `autor_solucion_kb` not empty | `autor_solucion` | `informativo` |
| 3 | `tipo = advertencia`, `repeticiones < umbral` | `eventos` | `advertencia` |
| 4 | `categoria = seguridad`, `tipo != informativo` | `accesos` | `advertencia` (except contractual Access security exceptions) |
| 5 | `categoria = solicitud_catalogo` | `peticiones` | `informativo` |
| 6 | `categoria = falla` | `incidencias` | `excepcion` |
| 7 | `repeticiones >= umbral` | `problemas` | `excepcion` |
| 8 | `categoria = cambio` | `peticiones` | `informativo` |
| 9 | none of the above | `incidencias` | `excepcion` |

- Conditions are evaluated in the order of section 3, not in numeric order.
- The output `tipo` is the classification assigned by the rule (section 2); the input `tipo` only takes part in rules 1 and 3.
- "Exceeding the threshold" is read as `repeticiones >= umbral`.

### 5. Edge cases and tests

| Case | Expected rule | Assigned type |
|---|---|---|
| Warning with `repeticiones = umbral - 1` | 3 | Warning |
| Warning with `repeticiones = umbral` | 7 | Exception (reclassified) |
| Repeated failure (`repeticiones >= umbral`) | 7 (not 6) | Exception |
| Security with a KB solution or repeated | 4 | Warning |
| User failure with a KB solution | 2 | Informational |
| User informational event without KB | 9 | Exception |
| System informational event with `requiere_accion = true` | 9 | Exception |
| Event with no match | 9 | Exception |

**Running the tests:**

```bash
cd services/events
make test
```

- Pending tests show up as `xfail` with their reason.
- Two guard tests (not `xfail`) check that all 9 rules have at least one case and that each rule's assigned type matches the table in section 2.

### 6. Assumptions and open decisions

- The evaluation order (section 3) is still to be confirmed with the team.
- Rule 7 is evaluated only by `repeticiones >= umbral`, not by "unknown root cause", so that not every new failure goes to Problems.
- Rule 7 ignores the input `tipo`: a repeated informational event would also reach Problems and be reclassified as Exception. To be confirmed whether it should be excluded.
- The output `tipo` is assigned by the rule; the input `tipo` is only used by rules 1 and 3.
- The rule 2 survey is not modeled in the engine: the destination is `autor_solucion` both when delivering the solution and when the answer is "not resolved".
- The alert channel used when the threshold is exceeded (rule 3) is not defined.
- The engine receives `repeticiones` already computed; N and T are external parameters.
- The KB must store the author of each article to fill `autor_solucion_kb`.

### 7. References

- [`ARCHITECTURE.md`](ARCHITECTURE.md): section 6, Events flow.
- [`ITIL-MAPPING.md`](ITIL-MAPPING.md): mapping of services to ITIL v4 practices.
- [`test_rules.py`](../services/events/tests/test_rules.py): parametrized rule tests.
