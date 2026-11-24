"""Registro de eventos: huella, deduplicación, clasificación, prioridad, SLA y reglas 1 y 3."""

import hashlib
import json

from django.db import IntegrityError, transaction
from django.utils import timezone

from ..models import (
    TERMINAL_STATES,
    ActorType,
    ChangeType,
    Event,
    EventCategory,
    EventState,
)
from ..priority import PriorityContext, resolve_priority
from .classification import classify_event_type, watch_warning
from .lifecycle import auto_close_informational, record_history
from .priority import priority_context, resolve_sla


def compute_fingerprint(origin, title, message, service_code, source_name, payload) -> str:
    fingerprint_input = json.dumps(
        {
            "origin": origin,
            "title": title,
            "message": message,
            "service_code": service_code,
            "source_name": source_name,
            "payload": payload,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()


def _find_open_event(fingerprint):
    return (
        Event.objects.select_for_update()
        .filter(fingerprint=fingerprint)
        .exclude(state__in=TERMINAL_STATES)
        .first()
    )


def _add_occurrence(open_event, event_dt, ingestion_key, actor_ref=""):
    """Suma una ocurrencia al evento abierto, recalcula la prioridad y aplica la regla 3."""
    previous_count = open_event.occurrence_count
    open_event.occurrence_count = previous_count + 1
    open_event.last_seen_at = event_dt
    if ingestion_key:
        stored_payload = dict(open_event.payload or {})
        stored_payload["_ingestion_key"] = ingestion_key
        open_event.payload = stored_payload
    update_fields = ["occurrence_count", "last_seen_at", "payload", "updated_at"]

    old_priority = open_event.priority
    result = resolve_priority(open_event.impact, open_event.urgency, priority_context(open_event))
    new_priority = result.priority.value if result.priority else old_priority
    if new_priority != old_priority:
        open_event.priority = new_priority
        update_fields.append("priority")
    open_event.save(update_fields=update_fields)

    if new_priority != old_priority:
        record_history(
            open_event,
            change_type=ChangeType.PRIORITY_CHANGE,
            actor_type=ActorType.SYSTEM,
            actor_ref=actor_ref,
            field_name="priority",
            old_value=old_priority or None,
            new_value=new_priority,
            description="Prioridad recalculada por recurrencia",
            metadata={"priority": result.as_metadata()},
        )
    watch_warning(open_event, previous_count=previous_count)
    return open_event


@transaction.atomic
def register_event(validated_data: dict, actor_ref: str = "") -> tuple[Event, bool]:
    """Registra un evento. Devuelve (evento, creado). creado=False si fue un duplicado."""
    now = timezone.now()
    event_dt = validated_data.get("occurred_at") or now
    clean_payload = dict(validated_data.get("payload") or {})
    ingestion_key = validated_data.get("ingestion_key")

    if ingestion_key:
        existing = Event.objects.filter(payload___ingestion_key=ingestion_key).first()
        if existing:
            return existing, False

    service = validated_data.get("service")
    source = validated_data.get("source")
    service_code = service.code if service else None
    source_name = source.name if source else None
    fingerprint = compute_fingerprint(
        validated_data["origin"],
        validated_data["title"],
        validated_data["message"],
        service_code,
        source_name,
        clean_payload,
    )

    open_event = _find_open_event(fingerprint)
    if open_event:
        return _add_occurrence(open_event, event_dt, ingestion_key, actor_ref), False

    event_type = classify_event_type(
        origin=validated_data["origin"],
        declared=validated_data.get("event_type"),
        payload=clean_payload,
    )
    category = validated_data.get("category") or EventCategory.GENERAL
    impact = validated_data.get("impact") or ""
    urgency = validated_data.get("urgency") or ""
    priority_result = resolve_priority(
        impact,
        urgency,
        PriorityContext(
            service_importance=service.importance if service else None,
            category=category,
            event_type=event_type,
            occurrence_count=1,
        ),
    )
    priority = priority_result.priority.value if priority_result.priority else ""
    sla_policy, response_due_at, resolution_due_at = resolve_sla(service, priority, event_dt)

    stored_payload = dict(clean_payload)
    if ingestion_key:
        stored_payload["_ingestion_key"] = ingestion_key

    try:
        with transaction.atomic():  # savepoint: un IntegrityError no rompe la transacción externa
            event = Event.objects.create(
                origin=validated_data["origin"],
                event_type=event_type,
                category=category,
                title=validated_data["title"],
                message=validated_data["message"],
                payload=stored_payload,
                service=service,
                source=source,
                impact=impact,
                urgency=urgency,
                priority=priority,
                state=EventState.NEW,
                action_required=validated_data.get("action_required", True),
                fingerprint=fingerprint,
                occurrence_count=1,
                first_seen_at=event_dt,
                last_seen_at=event_dt,
                sla_policy=sla_policy,
                response_due_at=response_due_at,
                resolution_due_at=resolution_due_at,
                closed_at=None,
                created_by_ref=actor_ref,
                updated_by_ref=actor_ref,
            )
    except IntegrityError:
        # Carrera: otra petición creó el evento abierto con esta huella entre la consulta y el
        # INSERT (restricción uq_event_open_fingerprint). Se cuenta como una ocurrencia más.
        open_event = _find_open_event(fingerprint)
        if open_event is None:
            raise
        return _add_occurrence(open_event, event_dt, ingestion_key, actor_ref), False

    record_history(
        event,
        change_type=ChangeType.SYSTEM,
        actor_type=ActorType.SYSTEM,
        actor_ref=actor_ref,
        to_state=EventState.NEW,
        description="Evento registrado",
        metadata={"priority": priority_result.as_metadata()} if priority else {},
    )
    event = auto_close_informational(event)  # regla 1: informativo de sistema sin acción
    watch_warning(event, previous_count=0)  # regla 3: advertencia, vigilancia y alerta
    return event, True
