# Publicación al broker (outbox + NATS JetStream)

> Práctica ITIL v4: Monitoring and Event Management. Contrato de mensajes:
> [`contracts/messages/event-envelope.json`](../../../contracts/messages/event-envelope.json).

Los demás servicios se enteran de lo que pasa en Eventos **sin acoplarse** (no llaman a Eventos ni
leen su BD) y **sin perder mensajes**, aunque el broker esté caído.

## 1. Cómo funciona

```
POST /events, transición, asignación, regla 1 ─┐  una sola transacción
                                               ├─► event / event_history
                                               └─► outbox_message (PENDING)

manage.py publish_outbox ─► lee PENDING vencidos ─► sobre común ─► JetStream (stream EVENTS)
   ├─ PubAck            → PUBLISHED (published_at)
   ├─ broker caído      → sigue PENDING; se reintenta en el próximo pase, en el mismo orden
   └─ mensaje inválido  → reintento con espera exponencial; tras OUTBOX_MAX_ATTEMPTS → FAILED
```

1. **Escritura** (`events/outbox/messages.py`): `register_event` y `transition_event` llaman a
   `enqueue_state_changed` dentro de su `transaction.atomic`. Si el cambio se revierte, el mensaje
   también; si el mensaje no se puede escribir, el cambio no se guarda.
2. **Publicación** (`events/outbox/relay.py`): un proceso aparte toma los mensajes `PENDING` cuyo
   `next_attempt_at` ya llegó y los pasa a un `Publisher`. Con PostgreSQL usa
   `SELECT ... FOR UPDATE SKIP LOCKED`, así dos publicadores no mandan lo mismo.
3. **Broker** (`events/outbox/jetstream.py`): JetStream guarda el mensaje y lo confirma (`PubAck`).
   Con NATS a secas, un mensaje sin suscriptores conectados se perdería.

## 2. Mensajes que se publican hoy

| Tipo | Subject | Cuándo |
|---|---|---|
| `event.state_changed` | `events.state_changed` | Alta del evento (`from_state` nulo → `NEW`) y cada transición, incluidas la asignación y el cierre automático de la regla 1 |
| `event.routed` | `events.routed.<destino>` (`access`, `requests`, `incidents`, `problems`) | Constructor listo (`enqueue_routed`); lo dispara el enrutamiento de las reglas 4–8 (fase 3) |

- Una ocurrencia duplicada **no** publica nada: no cambia el estado.
- Stream: `OUTBOX_STREAM` (por omisión `EVENTS`) con subjects `events.>`. Lo crea el publicador si
  no existe; si existe, no lo modifica. Retención: `OUTBOX_STREAM_MAX_AGE_DAYS` (7).
- Los consumidores (Peticiones, Incidencias, Problemas, Accesos) se suscriben con un consumidor
  duradero de JetStream a `events.>` o a su subject, p. ej. `events.routed.incidents`.

## 3. Idempotencia y garantía de entrega

- **Al menos una vez.** Se marca `PUBLISHED` solo después del `PubAck`. Si el proceso muere entre
  la confirmación y el guardado, el mensaje se reenvía.
- **El `id` del sobre es el `id` de `outbox_message`** y viaja también en la cabecera
  `Nats-Msg-Id`: JetStream descarta el duplicado dentro de su ventana (2 min por omisión).
- Fuera de esa ventana, **el consumidor deduplica por `id`** (tabla `processed_message` o similar).
- Orden: los mensajes salen por `created_at`. Una caída del broker no los desordena (se corta el
  pase sin reprogramar). Solo un mensaje con falla permanente puede quedar detrás de los siguientes.

## 4. Reintentos y errores

| Falla | Ejemplos | Qué pasa |
|---|---|---|
| Temporal (`TransientPublishError`) | Broker caído, timeout, JetStream no disponible | Se corta el pase, `attempts + 1` y `last_error`; sigue `PENDING` y vencido. **Nunca** pasa a `FAILED` por una caída |
| Permanente (otra excepción) | Mensaje mayor al máximo del servidor, subject inválido | `attempts + 1`, `last_error`, `next_attempt_at = ahora + espera`; al llegar a `OUTBOX_MAX_ATTEMPTS` → `FAILED`. El pase sigue con los demás |

- Espera: `OUTBOX_BACKOFF_BASE_SECONDS × 2^(intentos − 1)`, con tope `OUTBOX_BACKOFF_MAX_SECONDS`
  (5 s, 10 s, 20 s… hasta 15 min).
- Registro de errores: logs JSON (`outbox_broker_unavailable`, `outbox_publish_retry`,
  `outbox_message_failed`, `outbox_published`) con `message_id`, `subject`, `attempts` y `error`,
  y `last_error` en la fila.
- Los `FAILED` se revisan en `/admin/` (*Mensajes de salida*) y se reintentan con la acción
  **Reintentar (volver a PENDING)**.

## 5. Ejecutar el publicador

```bash
python manage.py publish_outbox                 # un pase: publica lo vencido y termina (CronJob)
python manage.py publish_outbox --loop          # worker continuo; termina limpio con SIGTERM
python manage.py publish_outbox --batch 100 --max-attempts 5 --url nats://localhost:4222
```

- Con `OUTBOX_TRANSPORT=jetstream` y sin `BROKER_URL`, o con rutas REST inválidas, el comando falla
  avisando y los mensajes siguen `PENDING`.
- En modo `--loop`, si el broker cae, reconecta con espera creciente (tope 60 s).
- **Despliegue:** el worker (`publish_outbox --loop`) debe correr junto al servicio en el compose
  local y en el chart de Helm. Esas carpetas son de Plataforma: se les pide por issue/PR; aquí solo
  vive el comando.

| Variable | Por omisión | Para qué |
|---|---|---|
| `OUTBOX_TRANSPORT` | `jetstream` | `jetstream` o `http` (plan B, sección 6) |
| `BROKER_URL` | vacío | `nats://broker:4222` (compose y Helm ya la inyectan); solo `jetstream` |
| `OUTBOX_HTTP_ROUTES` / `OUTBOX_HTTP_TOKEN` | vacío | Solo `http`: rutas por subject y token opcional |
| `OUTBOX_STREAM` | `EVENTS` | Nombre del stream de JetStream |
| `OUTBOX_STREAM_MAX_AGE_DAYS` | `7` | Retención del stream al crearlo |
| `OUTBOX_PUBLISH_TIMEOUT_SECONDS` | `5` | Conexión y confirmación del broker |
| `OUTBOX_BATCH_SIZE` | `50` | Mensajes por pase |
| `OUTBOX_MAX_ATTEMPTS` | `10` | Fallas permanentes antes de `FAILED` |
| `OUTBOX_BACKOFF_BASE_SECONDS` / `_MAX_SECONDS` | `5` / `900` | Espera exponencial |
| `OUTBOX_POLL_INTERVAL_SECONDS` | `2` | Pausa entre pases con `--loop` |

## 6. Plan B: publicación por REST

Si el broker se complica (ROADMAP, fase 2, riesgos), Eventos entrega cada mensaje con un `POST`
síncrono. **La interfaz es la misma** (`Publisher.publish(subject, body, message_id)`): no cambian
el outbox, la emisión de mensajes, los reintentos ni la espera exponencial; solo el transporte.

```bash
OUTBOX_TRANSPORT=http
OUTBOX_HTTP_ROUTES="events.routed.incidents=http://incidents:8004/api/incidents/v1/messages;events.state_changed=http://requests:8003/api/requests/v1/messages,http://incidents:8004/api/incidents/v1/messages"
OUTBOX_HTTP_TOKEN=            # opcional: Authorization: Bearer <token>
python manage.py publish_outbox --loop
```

- **Ruteo:** `patrón=url1,url2;patrón=url3`, con los comodines de NATS (`*` = un token, `>` = el
  resto), igual que una suscripción. Un subject sin ruta no tiene receptores y se da por entregado.
- **Petición:** `POST` con el **mismo sobre** (`event-envelope.json`) y las cabeceras
  `Idempotency-Key: <id del sobre>`, `X-Message-Subject: <subject>` y `Content-Type: application/json`.
- **Respuesta:** 2xx = entregado. Sin conexión, timeout, `408`, `429` o `5xx` = falla temporal (el
  mensaje sigue `PENDING`, en orden). Otro `4xx` = el receptor lo rechaza: falla permanente
  (reintento con espera y, al final, `FAILED`).
- **Varios receptores:** el mensaje se marca `PUBLISHED` solo si **todos** respondieron 2xx. En un
  reintento se reenvía a todos; los que ya lo tenían lo reconocen por `Idempotency-Key`.

**Lo que debe ofrecer cada receptor** (lo implementa cada equipo en su servicio si se activa el
plan B; Eventos no toca esas carpetas):

1. Un endpoint interno, p. ej. `POST /api/<servicio>/v1/messages`, que acepte el sobre común.
2. Deduplicar por `Idempotency-Key` (o `id` del sobre) y responder **2xx también a un duplicado**.
3. Responder `5xx`/`503` si no puede procesar por ahora (Eventos reintenta) y `4xx` solo si el
   mensaje es inválido.

| | JetStream (por omisión) | REST (plan B) |
|---|---|---|
| Acoplamiento | Ninguno: Eventos no conoce a los consumidores | Eventos conoce las URL de los receptores (`OUTBOX_HTTP_ROUTES`) |
| Receptor caído | El broker guarda el mensaje | El mensaje espera en `outbox_message` |
| Duplicados | `Nats-Msg-Id` + `id` del sobre | `Idempotency-Key` |
| Cambiar de uno a otro | `OUTBOX_TRANSPORT=jetstream` | `OUTBOX_TRANSPORT=http` |

## 7. Pruebas

| Archivo | Qué demuestra |
|---|---|
| `tests/test_outbox.py` | Mensaje en la misma transacción (rollback de ambos), orden NEW → CLOSED, sobre conforme a `event-envelope.json` |
| `tests/test_outbox_relay.py` | Broker caído: quedan `PENDING` y se envían después y en orden; reintentos, espera, `FAILED`; comando y worker que reconecta |
| `tests/test_outbox_jetstream.py` | Contra un NATS real: stream creado, deduplicación por `Nats-Msg-Id`, flujo completo registro → comando → stream |
| `tests/test_outbox_http.py` | Plan B contra un servidor HTTP real: ruteo con comodines, cabeceras de idempotencia, receptor caído (5xx/429/408/sin conexión) → `PENDING` y entrega posterior, 4xx → reintento, comando sin broker |

Con un broker desechable:

```bash
docker run --rm -p 4222:4222 docker.io/library/nats:2-alpine -js   # o podman run ...
NATS_TEST_URL=nats://127.0.0.1:4222 uv run pytest tests/test_outbox_jetstream.py
```

Sin `NATS_TEST_URL` esas pruebas se saltan (CI de Jenkins incluido).
