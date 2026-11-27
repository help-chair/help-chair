"""Registro de eventos: clasificación, huella, deduplicación, prioridad, SLA y reglas 1 y 3."""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from ..models import (
    ActorType,
    ChangeType,
    Event,
    EventCategory,
    EventOccurrence,
    EventState,
    MatchKind,
)
from ..outbox.messages import enqueue_state_changed
from ..priority import PriorityContext, resolve_priority
from .classification import classify_event_type, watch_warning
from .deduplication import (
    find_fuzzy_match,
    find_open_event_by_fingerprint,
    similar_event_count,
)

# from .dispatch import schedule_dispatch
from .fingerprint import compute_fingerprint
from .lifecycle import auto_close_informational, record_history
from .priority import priority_context, resolve_sla


def _add_occurrence(
    event, *, event_dt, payload, ingestion_key, kind, similarity=None, actor_ref=""
) -> Event:
    """Suma una ocurrencia a un evento abierto, recalcula la prioridad y aplica la regla 3."""
    EventOccurrence.objects.create(
        event=event,
        occurred_at=event_dt,
        fingerprint=event.fingerprint,
        match_kind=kind,
        similarity=similarity,
        payload=payload,
        ingestion_key=ingestion_key or "",
    )
    event.occurrence_count += 1
    event.last_seen_at = max(event.last_seen_at, event_dt)
    event.first_seen_at = min(event.first_seen_at, event_dt)
    if ingestion_key:
        stored_payload = dict(event.payload or {})
        stored_payload["_ingestion_key"] = ingestion_key
        event.payload = stored_payload
    update_fields = [
        "occurrence_count",
        "last_seen_at",
        "first_seen_at",
        "payload",
        "updated_at",
    ]

    # Más ocurrencias pueden subir la prioridad (modificador OCCURRENCE_COUNT).
    old_priority = event.priority
    result = resolve_priority(event.impact, event.urgency, priority_context(event))
    new_priority = result.priority.value if result.priority else old_priority
    if new_priority != old_priority:
        event.priority = new_priority
        update_fields.append("priority")
    event.save(update_fields=update_fields)

    if new_priority != old_priority:
        record_history(
            event,
            change_type=ChangeType.PRIORITY_CHANGE,
            actor_type=ActorType.SYSTEM,
            actor_ref=actor_ref,
            field_name="priority",
            old_value=old_priority or None,
            new_value=new_priority,
            description="Prioridad recalculada por recurrencia",
            metadata={"priority": result.as_metadata()},
        )
    if kind == MatchKind.FUZZY:
        record_history(
            event,
            change_type=ChangeType.SYSTEM,
            actor_type=ActorType.RULE,
            actor_ref="dedup",
            description=f"Ocurrencia fusionada por similitud ({similarity:.3f})",
            metadata={"match_kind": kind, "similarity": similarity},
        )
    count = similar_event_count(event)
    watch_warning(event, previous_count=count - 1, current_count=count)  # regla 3
    # schedule_dispatch(event.pk)  # si cruzó el umbral, la regla 7 lo enruta a Problemas
    return event


@transaction.atomic
def register_event(validated_data: dict, actor_ref: str = "") -> tuple[Event, bool]:
    """Registra un evento. Devuelve (evento, creado). creado=False si fue un duplicado."""
    now = timezone.now()
    event_dt = validated_data.get("occurred_at") or now
    clean_payload = dict(validated_data.get("payload") or {})
    ingestion_key = validated_data.get("ingestion_key")

    if ingestion_key:
        existing = (
            Event.objects.filter(
                Q(payload___ingestion_key=ingestion_key)
                | Q(occurrences__ingestion_key=ingestion_key)
            )
            .distinct()
            .first()
        )
        if existing:
            return existing, False

    service = validated_data.get("service")
    source = validated_data.get("source")
    category = validated_data.get("category") or EventCategory.GENERAL
    # El tipo se clasifica antes de la huella, porque la huella lo incluye.
    event_type = classify_event_type(
        origin=validated_data["origin"],
        declared=validated_data.get("event_type"),
        payload=clean_payload,
    )
    fingerprint = compute_fingerprint(
        event_type=event_type,
        origin=validated_data["origin"],
        source_name=source.name if source else None,
        service_code=service.code if service else None,
        title=validated_data["title"],
        message=validated_data["message"],
    )

    def merge(open_event, kind, similarity=None):
        return _add_occurrence(
            open_event,
            event_dt=event_dt,
            payload=clean_payload,
            ingestion_key=ingestion_key,
            kind=kind,
            similarity=similarity,
            actor_ref=actor_ref,
        )

    # Etapa 1: misma huella en un evento abierto. Etapa 2 (opcional): similitud.
    open_event = find_open_event_by_fingerprint(fingerprint)
    if open_event:
        return merge(open_event, MatchKind.EXACT), False
    fuzzy = find_fuzzy_match(
        event_type=event_type,
        origin=validated_data["origin"],
        category=category,
        source=source,
        service=service,
        title=validated_data["title"],
        message=validated_data["message"],
        event_dt=event_dt,
    )
    if fuzzy:
        return merge(fuzzy.event, fuzzy.kind, fuzzy.similarity), False

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
        open_event = find_open_event_by_fingerprint(fingerprint)
        if open_event is None:
            raise
        return merge(open_event, MatchKind.EXACT), False

    EventOccurrence.objects.create(
        event=event,
        occurred_at=event_dt,
        fingerprint=fingerprint,
        match_kind=MatchKind.NEW,
        payload=clean_payload,
        ingestion_key=ingestion_key or "",
    )
    record_history(
        event,
        change_type=ChangeType.SYSTEM,
        actor_type=ActorType.SYSTEM,
        actor_ref=actor_ref,
        to_state=EventState.NEW,
        description="Evento registrado",
        metadata={"priority": priority_result.as_metadata()} if priority else {},
    )
    enqueue_state_changed(  # alta: from_state nulo -> NEW, en la misma transacción
        event,
        from_state=None,
        to_state=EventState.NEW,
        actor_type=ActorType.SYSTEM,
        actor_ref=actor_ref,
        changed_at=event.created_at,
    )
    event = auto_close_informational(event)  # regla 1: informativo de sistema sin acción
    count = similar_event_count(event)
    watch_warning(event, previous_count=count - 1, current_count=count)  # regla 3
    # schedule_dispatch(event.pk)  # reglas 4 a 9: no hace nada si el evento ya se cerró (R1)
    return event, True
