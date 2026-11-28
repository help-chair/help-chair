"""Cambios de gestión sobre un evento: asignación, reclasificación y notas (PATCH)."""

from django.db import transaction

from ..models import TERMINAL_STATES, ActorType, ChangeType
from ..priority import resolve_priority
from .dispatch import schedule_dispatch
from .lifecycle import EventConflict, assign_event, lock_event, record_history
from .priority import priority_context, resolve_sla


@transaction.atomic
def reclassify_event(
    event,
    *,
    category=None,
    impact=None,
    urgency=None,
    actor_type=ActorType.USER,
    actor_ref="",
):
    """Cambia categoría, impacto y/o urgencia. Recalcula la prioridad y el SLA.

    `None` = no cambiar. Cada cambio queda en el historial (CLASSIFICATION, PRIORITY_CHANGE).
    """
    event = lock_event(event)
    if event.state in TERMINAL_STATES:
        raise EventConflict(f"No se puede reclasificar un evento en estado {event.state}")

    wanted = {"category": category, "impact": impact, "urgency": urgency}
    changes = {k: v for k, v in wanted.items() if v is not None and v != getattr(event, k)}
    if not changes:
        return event

    old = {name: getattr(event, name) for name in changes}
    for name, value in changes.items():
        setattr(event, name, value)

    old_priority = event.priority
    priority_metadata = None
    # La categoría también forma parte del contexto del motor, no solo impacto y urgencia.
    result = resolve_priority(event.impact, event.urgency, priority_context(event))
    new_priority = result.priority.value if result.priority else ""
    if new_priority:  # sin resultado del motor se conserva la prioridad actual
        event.priority = new_priority
        priority_metadata = {"priority": result.as_metadata()}
        policy, response_due, resolution_due = resolve_sla(
            event.service, new_priority, event.first_seen_at
        )
        if policy:
            event.sla_policy = policy
            event.response_due_at = response_due
            event.resolution_due_at = resolution_due
    event.updated_by_ref = actor_ref
    event.save()

    record_history(
        event,
        change_type=ChangeType.CLASSIFICATION,
        actor_type=actor_type,
        actor_ref=actor_ref,
        field_name="classification",
        old_value=old,
        new_value=changes,
        description="Reclasificación",
    )
    if event.priority != old_priority:
        record_history(
            event,
            change_type=ChangeType.PRIORITY_CHANGE,
            actor_type=actor_type,
            actor_ref=actor_ref,
            field_name="priority",
            old_value=old_priority or None,
            new_value=event.priority,
            description="Prioridad recalculada",
            metadata=priority_metadata or {},
        )
    return event


@transaction.atomic
def update_event(event, data: dict, *, actor_ref=""):
    """Aplica un PATCH validado: asignación, reclasificación y nota (en ese orden)."""
    if "assigned_to_ref" in data or "assigned_group_ref" in data:
        event = assign_event(
            event,
            assigned_to_ref=_clearable(data, "assigned_to_ref"),
            assigned_group_ref=_clearable(data, "assigned_group_ref"),
            actor_ref=actor_ref,
        )
    if any(key in data for key in ("category", "impact", "urgency")):
        event = reclassify_event(
            event,
            category=data.get("category"),
            impact=data.get("impact"),
            urgency=data.get("urgency"),
            actor_ref=actor_ref,
        )
    if data.get("note"):
        record_history(
            event,
            change_type=ChangeType.NOTE,
            actor_type=ActorType.USER,
            actor_ref=actor_ref,
            description=data["note"],
        )
    if any(key in data for key in ("category", "impact", "urgency")):
        schedule_dispatch(event.pk)
    return event


def _clearable(data, key):
    """No enviado -> None (sin cambio); null o "" -> "" (quitar); valor -> valor."""
    if key not in data:
        return None
    return data[key] or ""
