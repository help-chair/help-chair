"""Mensajes de salida de Eventos: primera mitad del patrón *outbox*.

`enqueue` escribe una fila en `outbox_message` dentro de la transacción en curso, así el
mensaje existe si y solo si se confirmó el cambio que lo originó: nunca hay un evento sin su
mensaje ni un mensaje de algo que se revirtió. Publicar es trabajo de `manage.py publish_outbox`.

Forma de los mensajes: contracts/messages/event-envelope.json (dueño: Equipo 1).
Subjects de NATS: `events.state_changed` y `events.routed.<destino>` (p. ej.
`events.routed.incidents`); todos caen en el stream de JetStream que cubre `events.>`.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from ..models import OutboxMessage
from ..models.choices import Destination

ORIGIN = "events"
SUBJECT_PREFIX = "events"

STATE_CHANGED = "event.state_changed"
ROUTED = "event.routed"

# event.routed solo se publica cuando el destino es otro servicio (contrato, EventRoutedPayload).
ROUTABLE_DESTINATIONS = (
    Destination.ACCESS,
    Destination.REQUESTS,
    Destination.INCIDENTS,
    Destination.PROBLEMS,
)


def _iso(value):
    return value.isoformat() if value else None


def _json_safe(data: dict) -> dict:
    """Convierte fechas, UUID y decimales a tipos JSON (lo que guardará JSONField)."""
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def enqueue(
    message_type: str,
    *,
    subject: str,
    aggregate_id,
    payload: dict,
    occurred_at=None,
    version: int = 1,
    correlation_id=None,
) -> OutboxMessage:
    """Deja un mensaje pendiente. Llamar dentro de la transacción del cambio que lo origina."""
    return OutboxMessage.objects.create(
        message_type=message_type,
        subject=subject,
        aggregate_id=aggregate_id,
        payload=_json_safe(payload),
        occurred_at=occurred_at or timezone.now(),
        version=version,
        correlation_id=correlation_id,
    )


# --- event.state_changed --------------------------------------------------------------
def state_changed_payload(event, *, from_state, to_state, actor_type, actor_ref, changed_at):
    return {
        "event_id": str(event.id),
        "from_state": from_state or None,
        "to_state": to_state,
        "closure_code": event.closure_code or None,
        "state_reason": event.state_reason or None,
        "changed_at": _iso(changed_at),
        "actor_type": actor_type,
        "actor_ref": actor_ref or None,
    }


def enqueue_state_changed(
    event, *, from_state, to_state, actor_type, actor_ref="", changed_at=None
) -> OutboxMessage:
    """Cada cambio de estado (incluido el alta como NEW, con `from_state` nulo)."""
    changed_at = changed_at or timezone.now()
    return enqueue(
        STATE_CHANGED,
        subject=f"{SUBJECT_PREFIX}.state_changed",
        aggregate_id=event.id,
        occurred_at=changed_at,
        payload=state_changed_payload(
            event,
            from_state=from_state,
            to_state=to_state,
            actor_type=actor_type,
            actor_ref=actor_ref,
            changed_at=changed_at,
        ),
    )


# --- event.routed ---------------------------------------------------------------------
def routed_payload(event, *, destination, rule_code: str) -> dict:
    if destination not in ROUTABLE_DESTINATIONS:
        raise ValueError(f"event.routed no aplica al destino {destination}")
    return {
        "event_id": str(event.id),
        "destination": destination,
        "rule_code": rule_code,
        "event_type": event.event_type,
        "category": event.category,
        "state": event.state,
        "priority": event.priority or None,
        "impact": event.impact or None,
        "urgency": event.urgency or None,
        "service_code": event.service.code if event.service_id else None,
        "title": event.title,
        "message": event.message,
        "action_required": event.action_required,
        "occurrence_count": event.occurrence_count,
        "fingerprint": event.fingerprint,
        "first_seen_at": _iso(event.first_seen_at),
        "last_seen_at": _iso(event.last_seen_at),
        "reporter_ref": event.reporter_ref or None,
        # Datos crudos tal como llegaron (sin las claves internas, p. ej. `_ingestion_key`).
        "payload": {k: v for k, v in (event.payload or {}).items() if not k.startswith("_")},
    }


def enqueue_routed(event, *, destination, rule_code: str) -> OutboxMessage:
    """Destino decidido por el motor de reglas hacia otro servicio (Peticiones, Incidencias...)."""
    return enqueue(
        ROUTED,
        subject=f"{SUBJECT_PREFIX}.routed.{destination.lower()}",
        aggregate_id=event.id,
        payload=routed_payload(event, destination=destination, rule_code=rule_code),
    )


# --- sobre común ----------------------------------------------------------------------
def envelope(message: OutboxMessage, *, published_at=None) -> dict:
    """El mensaje como lo pide event-envelope.json.

    `timestamp` es cuándo se publica y `occurred_at` cuándo ocurrió el hecho: un mensaje que
    esperó en el outbox (broker caído) los tiene distintos.
    """
    return {
        "id": str(message.id),
        "type": message.message_type,
        "version": message.version,
        "origin": ORIGIN,
        "timestamp": _iso(published_at or timezone.now()),
        "occurred_at": _iso(message.occurred_at),
        "correlation_id": str(message.correlation_id) if message.correlation_id else None,
        "payload": message.payload,
    }


def encode(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")
