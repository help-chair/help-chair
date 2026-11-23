import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    TERMINAL_STATES,
    ActorType,
    ChangeType,
    Event,
    EventCategory,
    EventHistory,
    EventState,
    EventType,
    PriorityMatrix,
    SlaPolicy,
)


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


@transaction.atomic
def register_event(validated_data: dict, actor_ref: str = "") -> tuple[Event, bool]:
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

    open_event = (
        Event.objects.select_for_update()
        .filter(fingerprint=fingerprint)
        .exclude(state__in=TERMINAL_STATES)
        .first()
    )
    if open_event:
        open_event.occurrence_count += 1
        open_event.last_seen_at = event_dt
        if ingestion_key:
            stored_payload = dict(open_event.payload or {})
            stored_payload["_ingestion_key"] = ingestion_key
            open_event.payload = stored_payload
        open_event.save(update_fields=["occurrence_count", "last_seen_at", "payload", "updated_at"])
        return open_event, False

    impact = validated_data.get("impact") or ""
    urgency = validated_data.get("urgency") or ""
    priority = ""
    if impact and urgency:
        priority_row = PriorityMatrix.objects.filter(impact=impact, urgency=urgency).first()
        if priority_row:
            priority = priority_row.priority

    sla_policy = None
    response_due_at = None
    resolution_due_at = None
    if priority:
        sla_policy = (
            SlaPolicy.objects.filter(service=service, priority=priority).first()
            if service
            else None
        )
        if not sla_policy:
            sla_policy = SlaPolicy.objects.filter(service__isnull=True, priority=priority).first()
        if sla_policy:
            response_due_at = event_dt + timedelta(minutes=sla_policy.response_minutes)
            resolution_due_at = event_dt + timedelta(minutes=sla_policy.resolution_minutes)

    stored_payload = dict(clean_payload)
    if ingestion_key:
        stored_payload["_ingestion_key"] = ingestion_key

    event = Event.objects.create(
        origin=validated_data["origin"],
        event_type=validated_data.get("event_type") or EventType.INFORMATION,
        category=validated_data.get("category") or EventCategory.GENERAL,
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
    EventHistory.objects.create(
        event=event,
        change_type=ChangeType.SYSTEM,
        actor_type=ActorType.SYSTEM,
        actor_ref=actor_ref,
        to_state=EventState.NEW,
        description="Evento registrado",
    )
    return event, True
