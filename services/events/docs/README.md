# Modelo de datos — Servicio de Eventos

## 1. Convenciones

| Tema | Decisión |
|---|---|
| Identificadores | `Event.id` es **UUID** (se comparte con otros servicios y viaja en los mensajes); el resto usa `bigint` autoincremental |
| Referencias a otros servicios | Campos `*_ref` (texto o UUID), **sin llave foránea**: cada servicio tiene su BD. Ejemplos: usuario (Accesos), artículo (KB), destino (Peticiones, Incidencias, Problemas) |
| Base de Conocimiento | Es de otro servicio (equipo de Problemas). Eventos la consulta **solo por API**; guarda `article_ref` y una instantánea (título, versión, autor) |
| Enumeraciones | `TextChoices` de Django guardados como texto (legibles en SQL); no se usan tipos `ENUM` de PostgreSQL |
| Fechas | `timestamptz` en UTC (`USE_TZ = True`) |
| Huella de auditoría | Todas las tablas de configuración y estado heredan `AuditModel`: `created_at`, `updated_at`, `created_by_ref`, `updated_by_ref` |
| Huella de deduplicación | `fingerprint` (SHA-256 en hexadecimal, 64 caracteres) en `event` y `event_occurrence` |
| Series de tiempo | Solo `event_occurrence` es *hypertable* de TimescaleDB |

## 2. Ciclo de vida de un evento

![Ciclo de vida de un evento](diagrams/life_cycle_event.png)


## 3. Diagrama entidad-relación

![Diagrama entidad-relación](diagrams/Related_entity.png)


## 4. Diagrama de tablas

![Diagrama de tablas](diagrams/Table_Diagram.webp)


Las transiciones permitidas se definen **en código** (un diccionario `ALLOWED_TRANSITIONS`), no en una tabla. Un evento de usuario cerrado recibe encuesta; uno cancelado recibe los motivos; uno de sistema no recibe respuesta.

## 5. Enumeraciones

| Enum | Valores |
|---|---|
| `EventOrigin` | `USER`, `SYSTEM` |
| `EventType` (ITIL) | `INFORMATION`, `WARNING`, `EXCEPTION` |
| `EventCategory` | `SECURITY`, `REQUEST`, `FAILURE`, `CHANGE`, `GENERAL` |
| `EventState` | `NEW`, `ASSIGNED`, `IN_PROGRESS`, `ON_HOLD`, `RESOLVED`, `CLOSED`, `REJECTED`, `CANCELLED`, `REOPENED` |
| `Impact` / `Urgency` | `HIGH`, `MEDIUM`, `LOW` |
| `Priority` | `CRITICAL` (P1), `HIGH` (P2), `MEDIUM` (P3), `LOW` (P4) |
| `ServiceImportance` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `Destination` (docs/rules.md) | `LOG_ONLY`, `SOLUTION_AUTHOR`, `EVENTS`, `ACCESS`, `REQUESTS`, `INCIDENTS`, `PROBLEMS` |
| `RoutingStatus` | `PENDING`, `SENT`, `ACKNOWLEDGED`, `FAILED` |
| `ClosureCode` | `AUTO_LOGGED`, `KB_RESOLVED`, `SOLVED`, `NOT_APPLICABLE` |
| `ChangeType` | `STATE_CHANGE`, `ASSIGNMENT`, `PRIORITY_CHANGE`, `CLASSIFICATION`, `ROUTING`, `NOTE`, `SYSTEM` |
| `ActorType` | `USER`, `SYSTEM`, `RULE` |
| `SurveySource` | `KB_RESPONSE`, `CLOSURE` |
| `OutboxStatus` | `PENDING`, `PUBLISHED`, `FAILED` |
| `RecurrenceAction` | `WATCH_ALERT`, `CREATE_PROBLEM` |
| `SourceKind` | `SERVICE`, `WEBHOOK`, `USER_FORM`, `INTERNAL` |

## 6. Diccionario de datos

### `business_service` (antes `ImportanceService`)
Servicio de TI del catálogo de la empresa, con su importancia (definida en el onboarding).

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| code | slug | no | único |
| name | varchar(120) | no | |
| description | text | sí | |
| importance | enum | no | usada como modificador de prioridad |
| owner_department_ref | varchar(64) | sí | departamento (vive en Accesos) |
| is_active | bool | no | por defecto `true` |
| huella de auditoría | | | `created_at`, `updated_at`, `created_by_ref`, `updated_by_ref` |

### `sla_policy`
Tiempos objetivo por prioridad; `service` nulo = política por defecto de la empresa.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| service_id | FK `business_service` | sí | |
| priority | enum | no | |
| response_minutes | int | no | |
| resolution_minutes | int | no | |
| uses_business_hours | bool | no | `false` = 24×7 (versión mínima) |
| auditoría | | | |

Restricción: único (`service`, `priority`). Para `service` nulo, agregar una restricción única parcial sobre `priority`.

### `priority_matrix` (antes `MatrixPriority`)
Prioridad base a partir de impacto × urgencia.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| impact | enum | no | |
| urgency | enum | no | |
| priority | enum | no | |
| auditoría | | | |

Restricción: único (`impact`, `urgency`). Siembra de 9 filas con `make seed`.

### `priority_modifier`
«Modificadores» del cálculo de prioridad (diagrama 2).

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| code | varchar(50) | no | único |
| condition_field | enum | no | `SERVICE_IMPORTANCE`, `EVENT_CATEGORY`, `EVENT_TYPE`, `OCCURRENCE_COUNT` |
| condition_value | varchar(50) | no | por ejemplo `CRITICAL` o `10` |
| levels_delta | smallint | no | `+1` sube un nivel, `-1` baja uno |
| is_active | bool | no | |
| auditoría | | | |

### `recurrence_policy`
Umbral y ventana T para las reglas 3 y 7 (advertencia bajo el umbral y patrón repetido).

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| event_type, category | enum | sí | nulo = aplica a cualquiera |
| service_id | FK `business_service` | sí | |
| threshold_count | int | no | N |
| window_days | int | no | T |
| action | enum | no | `WATCH_ALERT` o `CREATE_PROBLEM` |
| is_active | bool | no | |
| auditoría | | | |

### `event_source` (fase 4)
Fuentes registradas, para la ingesta por webhook con clave de API.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| name | varchar(100) | no | único |
| kind | enum | no | |
| api_key_hash | varchar(128) | sí | se guarda solo el hash |
| is_active | bool | no | |
| auditoría | | | |

### `event` (estado actual, un registro por evento deduplicado)

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | uuid PK | no | |
| origin | enum | no | usuario o sistema |
| event_type | enum | no | informativo, advertencia, excepción |
| category | enum | no | seguridad, petición, general |
| title / message | varchar(200) / text | no | |
| payload | jsonb | no | datos crudos |
| service_id | FK `business_service` | sí | |
| source_id | FK `event_source` | sí | |
| impact / urgency | enum | sí | entradas de la matriz |
| priority | enum | sí | calculada |
| state | enum | no | por defecto `NEW` |
| action_required | bool | no | `false` = informativo sin acción |
| fingerprint | char(64) | no | huella de deduplicación |
| occurrence_count | int | no | contador, inicia en 1 |
| first_seen_at / last_seen_at | timestamptz | no | |
| reporter_ref | varchar(64) | sí | sujeto a notificar |
| assigned_to_ref / assigned_group_ref | varchar(64) | sí | |
| sla_policy_id | FK `sla_policy` | sí | |
| response_due_at / resolution_due_at | timestamptz | sí | |
| resolved_at | timestamptz | sí | |
| **closed_at** | timestamptz | sí | es `fecha_cierre`, **nula al registrar** |
| closure_code | enum | sí | |
| state_reason | text | sí | motivo de rechazo o cancelación |
| auditoría | | | |

Índices y restricciones:
- **Único parcial** sobre `fingerprint` donde `state` no es `CLOSED`, `REJECTED` ni `CANCELLED` (un solo evento abierto por huella).
- (`state`), (`state`, `priority`), (`service_id`, `state`), (`assigned_to_ref`, `state`), (`created_at` descendente) y (`resolution_due_at`) donde el evento está abierto.
### `event_occurrence` (hypertable de TimescaleDB)
Cada llegada cruda de un evento. Permite calcular `n_eventos_similares` en una ventana T, analizar tendencias y aplicar retención.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint | no | parte de la llave primaria |
| occurred_at | timestamptz | no | parte de la llave primaria y **columna de partición** |
| event_id | FK `event` | no | `PROTECT` |
| fingerprint | char(64) | no | |
| source | varchar(100) | no | |
| payload | jsonb | no | |
| ingestion_key | varchar(100) | sí | idempotencia; único junto con `occurred_at` |
| received_at | timestamptz | no | |

Índices: (`fingerprint`, `occurred_at` descendente), (`event_id`, `occurred_at` descendente).

### `event_history` (antes `EventsHistory`)
Bitácora de cambios, solo de inserción.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| event_id | FK `event` | no | |
| changed_at | timestamptz | no | |
| change_type | enum | no | |
| actor_type / actor_ref | enum / varchar(64) | no / sí | usuario, sistema o regla |
| from_state / to_state | enum | sí | |
| field_name | varchar(60) | sí | |
| old_value / new_value | jsonb | sí | |
| description | text | sí | |
| rule_code | varchar(20) | sí | por ejemplo `R6` |
| metadata | jsonb | no | |

### `event_routing`
Trazabilidad de la decisión de destino (reglas 1–9) y de su entrega.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| event_id | FK `event` | no | |
| destination | enum | no | |
| rule_code | varchar(20) | no | regla aplicada |
| status | enum | no | |
| destination_ref | varchar(64) | sí | ID en el servicio destino (o el autor, si el destino es `SOLUTION_AUTHOR`) |
| attempts | int | no | |
| last_error | text | sí | |
| routed_at | timestamptz | sí | |
| auditoría | | | |

### `event_kb_response`
Auto-respuesta con artículo de la KB (regla 2) y su resultado. Eventos **no** guarda artículos: consulta la API del servicio de KB, registra qué mostró y si ayudó, y enruta el evento al **autor de la solución y a su departamento** (regla 2) cuando el usuario responde «no me sirvió».

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| event_id | FK `event` | no | |
| article_ref | varchar(64) | no | ID del artículo (vive en la BD de la KB; **sin llave foránea**) |
| article_title | varchar(200) | sí | instantánea al momento de mostrarlo |
| article_version | varchar(30) | sí | versión del artículo mostrado |
| author_ref | varchar(64) | sí | autor de la solución en la KB (referencia a Accesos): **destino de la regla 2** |
| department_ref | varchar(64) | sí | departamento del autor (referencia a Accesos); pasa a ser el grupo asignado del evento |
| presented_at | timestamptz | no | |
| helped | bool | sí | nulo = sin respuesta; `false` = «no me sirvió» |
| responded_at | timestamptz | sí | |
| auditoría | | | |

### `event_survey`
Encuesta de satisfacción (tras la auto-respuesta o al cerrar).

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | bigint PK | no | |
| event_id | FK `event` | no | |
| source | enum | no | |
| rating | smallint | sí | 1 a 5 |
| comment | text | sí | |
| respondent_ref | varchar(64) | sí | |
| answered_at | timestamptz | sí | |
| auditoría | | | |

### `outbox_message`
Patrón *outbox*: el mensaje se guarda en la misma transacción que el evento y se publica después.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| id | uuid PK | no | también es el `id` del sobre y la clave de idempotencia (`Nats-Msg-Id`, `Idempotency-Key`) |
| aggregate_id | uuid | no | el `event.id` |
| message_type | varchar(80) | no | `event.state_changed`, `event.routed` |
| version | smallint | no | versión del payload; por defecto `1` |
| subject | varchar(120) | no | `events.state_changed`, `events.routed.<destino>` |
| payload | jsonb | no | conforme a `contracts/messages/` |
| occurred_at | timestamptz | no | cuándo ocurrió el hecho (el `timestamp` del sobre es cuándo se publica) |
| correlation_id | uuid | sí | |
| status | enum | no | `PENDING`, `PUBLISHED`, `FAILED` |
| attempts | int | no | intentos de publicación |
| next_attempt_at | timestamptz | no | siguiente intento (espera exponencial tras una falla permanente) |
| last_error | text | sí | último error de publicación |
| created_at / published_at | timestamptz | no / sí | |

Índices: (`status`, `next_attempt_at`) y (`aggregate_id`, `created_at`). Migración `0004_outbox_message`. Funcionamiento, reintentos y plan B: [`outbox.md`](outbox.md).

### `processed_message`
Idempotencia del consumidor (evita procesar dos veces un mensaje, por ejemplo los eventos de login de Accesos).

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| message_id | uuid PK | no | |
| consumer | varchar(80) | no | |
| processed_at | timestamptz | no | |

## 7. Qué entra en cada fase

| Fase | Tablas |
|---|---|
| 1 | `business_service`, `sla_policy`, `priority_matrix`, `event`, `event_history` |
| 2 | `event_occurrence` (hypertable), `recurrence_policy`, `priority_modifier`, `outbox_message` |
| 3 | `event_routing`, `event_kb_response`, `event_survey`, `processed_message` |
| 4 | `event_source` y, si hace falta, `event_notification` |

### Ejecución local y verificación (fase 1)

Todos los comandos se ejecutan en `services/events/`, salvo los de `podman compose`, que se ejecutan en la raíz del repositorio.

#### 1. Preparar el entorno

```bash
make setup        # crea .env desde .env.example e instala dependencias (con uv, o venv + pip si no hay uv)
make help         # lista todos los comandos
```

#### 2. Calidad de código y chequeos (sin base de datos)

```bash
make lint                                                  # ruff check + ruff format --check
uv run python manage.py check                              # "System check identified no issues"
uv run python manage.py makemigrations --check --dry-run   # "No changes detected": los modelos y las migraciones coinciden
```

Si no usas uv, quita el prefijo `uv run`.

#### 3. Pruebas

```bash
make test                                   # pytest con cobertura
uv run pytest -q -rxX                       # además muestra los casos xfail/xpass
uv run pytest tests/test_rules.py --collect-only -q | tail -5   # cuántos casos de las 9 reglas hay
```

- `tests/test_health.py` debe quedar en verde.
- `tests/test_rules.py` contiene las 9 reglas de destino como pruebas parametrizadas (TDD). Las que aún no estén implementadas deben ir marcadas `xfail` con un motivo; así `make test` queda en verde sin ocultar el trabajo pendiente.
- Sin `DATABASE_URL` las pruebas usan SQLite. Para repetirlas contra PostgreSQL/TimescaleDB, sigue el paso 4 y vuelve a ejecutar `make test`.
#### 4. Base de datos (PostgreSQL + TimescaleDB)

Desde la raíz del repositorio:

```bash
podman compose -f platform/deploy/local/compose.yaml config --services   # confirma el nombre del servicio (events-db)
podman compose -f platform/deploy/local/compose.yaml up -d events-db
podman ps --format '{{.Names}}  {{.Status}}'                              # debe mostrar Up (healthy)
```

En `services/events/.env` descomenta o define:

```bash
DATABASE_URL=postgresql://events:events@localhost:5441/events
```

#### 5. Migraciones

```bash
make migrate                                          # aplica las migraciones
make seed                                             # matriz de prioridad y modificadores por defecto (manage.py seed_priority)
uv run python manage.py showmigrations events         # todas con [X]
uv run python manage.py makemigrations --check --dry-run   # sigue sin cambios
```

Verifica en la base de datos:

```bash
podman exec -it <contenedor-bd> psql -U events -d events -c "\dx"          # debe listar timescaledb
podman exec -it <contenedor-bd> psql -U events -d events -c "\dt"          # tablas de events + las de Django
podman exec -it <contenedor-bd> psql -U events -d events -c "\d event"     # revisa closed_at (nulo), índices y llaves foráneas
```

El nombre real del contenedor aparece en `podman ps`.

> **Si cambiaste migraciones que ya habías aplicado**, la base queda inconsistente. Reinicia el volumen (borra los datos locales de **todos** los servicios del compose):
> `podman compose -f platform/deploy/local/compose.yaml down -v` y vuelve a ejecutar `make migrate`.
> Nunca edites una migración que ya esté fusionada en `develop`: crea una nueva con `make makemigrations`.

Prueba de la restricción de deduplicación (un solo evento abierto por huella):

```bash
uv run python manage.py shell -c "
from django.db import IntegrityError, transaction
from events.models import Event
Event.objects.create(origin='SYSTEM', event_type='EXCEPTION', title='a', message='x', fingerprint='f'*64)
try:
    with transaction.atomic():
        Event.objects.create(origin='SYSTEM', event_type='EXCEPTION', title='b', message='x', fingerprint='f'*64)
    print('ERROR: permitió un duplicado abierto')
except IntegrityError:
    print('OK: rechaza el duplicado abierto')
Event.objects.filter(fingerprint='f'*64).delete()
"
```

#### 6. Health checks

```bash
make run                                          # servidor en http://localhost:8001 (aplica migraciones al arrancar)
```

En otra terminal:

```bash
curl -i http://localhost:8001/health/live         # 200
curl -i http://localhost:8001/health/ready        # 200 con la BD arriba
podman stop <contenedor-bd>
curl -i http://localhost:8001/health/ready        # 503: demuestra que verifica la BD
podman start <contenedor-bd>
```

#### 7. Admin de Django

```bash
uv run python manage.py createsuperuser
```

Entra a <http://localhost:8001/admin/>. Deben verse los modelos registrados (servicios, políticas de SLA, matriz de prioridad, fuentes, eventos e historial). Crea un evento y confirma que nace en estado **Nuevo** y con `closed_at` vacío.

#### 8. Imagen de contenedor y stack completo

```bash
make build                                                        # imagen ghcr.io/help-chair/hc-events:dev (Podman)
podman compose -f platform/deploy/local/compose.yaml up -d --build events    # desde la raíz
curl -i http://localhost:8001/health/ready
podman compose -f platform/deploy/local/compose.yaml down
```

#### Checklist de la puerta de salida de la fase 1

| Entregable | Cómo comprobarlo |
|---|---|
| Proyecto Django + DRF con ajustes por entorno | `make run`, `manage.py check` |
| Conexión a su PostgreSQL y migración inicial aplicada | Pasos 4 y 5 |
| `/health/live` y `/health/ready` (este verifica la BD) | Paso 6 (503 con la BD detenida) |
| `Dockerfile` (no root, gunicorn) y `Makefile` | `make build`, `make lint test` |
| `.env.example`, ruff + pre-commit, pytest con una prueba pasando | Pasos 1 a 3 |
| Modelo de datos y diagrama entidad-relación | `docs/README.md` y migraciones |
| Las 9 reglas como pruebas parametrizadas | `tests/test_rules.py` (`xfail` donde falte implementación) |
| Borrador OpenAPI y esquema del mensaje común | `contracts/events/openapi.yaml`, `contracts/messages/` (`make openapi`) |

### Prioridad de eventos

La prioridad (P1 a P4) se calcula al registrar un evento en `events/priority.py`, en dos pasos:

1. **Base:** la matriz impacto × urgencia (`PriorityMatrix`, tabla `priority_matrix`) da la prioridad base. Si el evento no trae impacto **y** urgencia, queda sin prioridad.
2. **Modificadores:** cada modificador activo (`PriorityModifier`, tabla `priority_modifier`) cuya condición se cumple suma `levels_delta` niveles (`+1` sube de P3 a P2; `-1` baja de P2 a P3). Los niveles se acumulan y el resultado se limita al rango P1–P4.

| `condition_field` | `condition_value` | Se cumple cuando |
|---|---|---|
| `SERVICE_IMPORTANCE` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` | la importancia del servicio afectado es ese valor |
| `EVENT_CATEGORY` | `SECURITY`, `REQUEST`, `FAILURE`, `CHANGE`, `GENERAL` | la categoría del evento es ese valor |
| `EVENT_TYPE` | `INFORMATION`, `WARNING`, `EXCEPTION` | el tipo del evento es ese valor |
| `OCCURRENCE_COUNT` | entero mayor que cero | `occurrence_count >= condition_value` |

- **Importancia por empresa:** cada empresa tiene su propia BD, así que la importancia de cada servicio (`BusinessService.importance`), la matriz y los modificadores son propios de la empresa. Se editan desde `/admin/`.
- **Recurrencia:** al deduplicar un evento abierto, la prioridad se recalcula con el nuevo `occurrence_count`; si cambia, se registra un `PRIORITY_CHANGE` en el historial con el valor anterior y el nuevo.
- **Trazabilidad:** el historial guarda en `metadata.priority` la base, la prioridad final, los niveles y los códigos de los modificadores aplicados.
- **Validación:** `levels_delta` va de `-3` a `3` y no puede ser `0`; `condition_value` debe ser válido para su `condition_field`.
- **Detalle:** `GET /api/v1/events/{id}` devuelve `priority` junto con `service.importance`.

**Valores por defecto (`make seed` o `manage.py seed_priority`):**

| Impacto \ Urgencia | `HIGH` | `MEDIUM` | `LOW` |
|---|---|---|---|
| `HIGH` | P1 | P2 | P3 |
| `MEDIUM` | P2 | P3 | P4 |
| `LOW` | P3 | P4 | P4 |

| Modificador | Condición | Niveles |
|---|---|---|
| `servicio-critico` | `SERVICE_IMPORTANCE = CRITICAL` | `+1` |
| `servicio-baja-importancia` | `SERVICE_IMPORTANCE = LOW` | `-1` |
| `recurrencia-10` | `OCCURRENCE_COUNT >= 10` | `+1` |

- La siembra es idempotente: solo crea lo que falta y no pisa la configuración de la empresa. `seed_priority --reset` restablece los valores por defecto.
- Pruebas: `tests/test_priority.py` (tabla de casos del cálculo, límites P1–P4, validación, siembra e integración con el registro y el detalle).

### Mock del contrato OpenAPI (Prism)

Los demás equipos (Frontend, Peticiones, Incidencias, Problemas y Accesos) pueden trabajar contra Eventos **sin esperar la implementación**: Prism lee `contracts/events/openapi.yaml` y responde con los ejemplos del contrato, validando además lo que recibe (401 sin token, 422 con cuerpo inválido). No usa base de datos ni el servicio Django.

#### 1. Levantar el mock con Podman (sin instalar nada en el host)

Funciona desde cualquier carpeta del repositorio:

```bash
podman run --rm -it --name hc-events-mock -p 8011:4010 \
  -v "$(git rev-parse --show-toplevel)/contracts/events/openapi.yaml:/spec/openapi.yaml:ro,Z" \
  docker.io/stoplight/prism:4 mock -h 0.0.0.0 /spec/openapi.yaml
```

| Opción | Para qué sirve |
|---|---|
| `--rm` | Elimina el contenedor al detenerlo |
| `-it` | TTY interactiva: `Ctrl + C` detiene el mock limpiamente |
| `--name hc-events-mock` | Nombre fijo para detenerlo fácilmente |
| `-p 8011:4010` | Expone el puerto interno de Prism (4010) en el `8011` del host |
| `-v ...:ro,Z` | Monta el contrato de solo lectura; `Z` aplica la etiqueta de SELinux (Fedora) |
| `-h 0.0.0.0` | Prism escucha en todas las interfaces dentro del contenedor |
| `docker.io/stoplight/prism:4` | Nombre completo de la imagen: evita que Podman pregunte de qué registro descargarla |

Sin contenedores (requiere Node.js), desde `services/events`:

```bash
npx @stoplight/prism-cli mock ../../contracts/events/openapi.yaml -p 8011
```

El mock queda en `http://127.0.0.1:8011`. **Las rutas no llevan el prefijo `/api/events/v1`** (por ejemplo, `/events`, no `/api/events/v1/events`).

#### 2. Probarlo con `curl` (en otra terminal)

Usa `127.0.0.1` y `-4` para evitar problemas con IPv6 (`::1`) en Podman rootless.

```bash
B=http://127.0.0.1:8011
H='Authorization: Bearer x'

# Evento nuevo (201). Sin "Prefer" responde 200 (el caso "duplicado"): ver la nota de abajo
curl -i -4 -X POST $B/events -H "$H" -H 'Content-Type: application/json' \
  -H 'Prefer: code=201' -d '{"origin":"USER","title":"t","message":"m"}'

# Lista y detalle
curl -i -4 "$B/events?state=NEW&limit=5" -H "$H"
curl -i -4 $B/events/7c9e6679-7425-40de-944b-e07fc1f90ae7 -H "$H"

# Transición inválida simulada (409)
curl -i -4 -X POST $B/events/7c9e6679-7425-40de-944b-e07fc1f90ae7/transitions \
  -H "$H" -H 'Content-Type: application/json' -H 'Prefer: code=409' -d '{"to_state":"IN_PROGRESS"}'

# El mock valida la entrada
curl -i -4 -X POST $B/events -H "$H" -H 'Content-Type: application/json' -d '{"origin":"USER","title":"t"}'   # 422 (falta message)
curl -i -4 $B/events                                                                                         # 401 (sin token)
```

**Cómo elige Prism la respuesta:**
- Por defecto devuelve el código **2xx más bajo** del contrato. Para `POST /events` es el `200` (evento duplicado); usa `-H 'Prefer: code=201'` para el evento nuevo.
- `-H 'Prefer: code=<código>'` fuerza cualquier otra respuesta definida (409, 404, 403…).
- Devuelve los `example` del contrato; donde no hay ejemplo genera datos de relleno (`"string"`).
#### 3. Revisar la cabecera `sl-violations`

Prism añade `sl-violations` cuando su respuesta **no cumple el esquema del propio contrato**. Con el contrato actual no debe aparecer:

```bash
curl -si -4 -X POST $B/events -H "$H" -H 'Content-Type: application/json' -H 'Prefer: code=201' \
  -d '{"origin":"USER","title":"t","message":"m"}' | grep -i '^sl-violations' || echo "sin violaciones"
```

Si aparece, hay un defecto en el contrato. Caso típico: un campo que puede ser `null` (por ejemplo `closure_code`) declarado con `allOf` + `nullable: true`, que en OpenAPI 3.0 **no** admite `null`. Se declara con un enum que incluya `null` (`ClosureCodeNullable`, `PriorityNullable`…). `tests/test_contracts.py` lo vigila.

#### 4. Detener el mock

- `Ctrl + C` en la terminal donde corre.
- Si quedó en segundo plano o suspendido: `podman stop hc-events-mock`.
#### 5. Usarlo desde otros servicios y desde el Frontend

- **Servicios:** apunta el cliente HTTP de pruebas a `http://127.0.0.1:8011` (sin el prefijo `/api/events/v1`).
- **Frontend:** el proxy de desarrollo (`/api/events`) reenvía sin reescribir rutas y solo el gateway tiene una opción para quitar el prefijo (`VITE_GATEWAY_MOCK`). Mientras no exista una equivalente para Eventos, llama al mock directamente.
#### 6. Validar el contrato

```bash
cd services/events
uv run openapi-spec-validator ../../contracts/events/openapi.yaml   # debe imprimir: ...openapi.yaml: OK
make test                                                            # incluye tests/test_contracts.py
```

#### Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| Podman pregunta de qué registro descargar la imagen | Usa el nombre completo `docker.io/stoplight/prism:4` |
| `permission denied` al leer `/spec/openapi.yaml` | Falta `:Z` en el volumen (SELinux) |
| `curl: (7)` o `(56)` sin respuesta | Usa `127.0.0.1` y `-4` en lugar de `localhost` |
| `address already in use` | Cambia el puerto del host: `-p 8012:4010` |
| 404 en `/api/events/v1/events` | El mock no usa el prefijo: llama a `/events` |
| El mock no refleja mis cambios al contrato | Prism no recarga el archivo: detén el mock y vuelve a levantarlo |

---

## English

### Running locally and verifying (phase 1)

Run everything inside `services/events/`, except the `podman compose` commands, which run from the repository root.

```bash
make setup                                                  # creates .env and installs dependencies (uv, or venv + pip)
make lint && make test                                      # ruff + pytest
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run    # "No changes detected"

# database (PostgreSQL + TimescaleDB), from the repo root
podman compose -f platform/deploy/local/compose.yaml up -d events-db
# in services/events/.env:  DATABASE_URL=postgresql://events:events@localhost:5441/events

make migrate && uv run python manage.py showmigrations events
make run                                                    # http://localhost:8001
curl -i http://localhost:8001/health/live                   # 200
curl -i http://localhost:8001/health/ready                  # 200 with the DB up, 503 with the DB stopped
```

- Without `DATABASE_URL` the tests use SQLite; repeat `make test` against PostgreSQL after starting `events-db`.
- If you changed migrations you had already applied, reset the volume: `podman compose -f platform/deploy/local/compose.yaml down -v`, then `make migrate`.
- Never edit a migration that is already merged into `develop`; create a new one with `make makemigrations`.
- Admin: `uv run python manage.py createsuperuser`, then <http://localhost:8001/admin/>.
- Image: `make build` (Podman) and `podman compose -f platform/deploy/local/compose.yaml up -d --build events`.

### OpenAPI contract mock (Prism)

Other teams can work against Events **without waiting for the implementation**: Prism reads `contracts/events/openapi.yaml`, answers with the contract's examples and validates what it receives (401 without a token, 422 for an invalid body). No database, no Django service.

```bash
# from anywhere inside the repository
podman run --rm -it --name hc-events-mock -p 8011:4010 \
  -v "$(git rev-parse --show-toplevel)/contracts/events/openapi.yaml:/spec/openapi.yaml:ro,Z" \
  docker.io/stoplight/prism:4 mock -h 0.0.0.0 /spec/openapi.yaml

# without containers (Node.js), from services/events
npx @stoplight/prism-cli mock ../../contracts/events/openapi.yaml -p 8011
```

- The mock listens on `http://127.0.0.1:8011`; **routes have no `/api/events/v1` prefix** (`/events`).
- `Z` applies the SELinux label (Fedora); use the full image name `docker.io/stoplight/prism:4` so Podman does not prompt for a registry.
- Prism returns the **lowest 2xx** by default: `POST /events` answers `200` (duplicate); add `-H 'Prefer: code=201'` for a new event. `Prefer: code=<n>` forces any other documented response.
- Test with `curl -i -4 http://127.0.0.1:8011/events -H 'Authorization: Bearer x'`.
- The `sl-violations` response header means the mock response does not match the contract's own schema; it must not appear. A nullable field declared with `allOf` + `nullable: true` is the typical cause (OpenAPI 3.0 rejects `null` there): use an enum that includes `null`.
- Stop with `Ctrl + C` or `podman stop hc-events-mock`. Prism does not reload the file: restart it after editing the contract.
- Validate the contract: `uv run openapi-spec-validator ../../contracts/events/openapi.yaml` and `make test`.
