"""Ciclo de vida del evento: transiciones, asignación y cierre automático (regla 1).

Lógica de negocio sobre el modelo; las vistas solo traducen HTTP a estas funciones.
Referencias: docs/rules.md (regla 1) y el diagrama de ciclo de vida de docs/README.md.
"""

from django.db import transaction
from django.utils import timezone

from ..models import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    ActorType,
    ChangeType,
    ClosureCode,
    Event,
    EventHistory,
    EventOrigin,
    EventState,
    EventType,
)

# Estados desde los que se puede (re)asignar un evento.
ASSIGNABLE_STATES = {
    EventState.NEW,
    EventState.ASSIGNED,
    EventState.IN_PROGRESS,
    EventState.ON_HOLD,
    EventState.REOPENED,
}
# Al asignar desde estos estados, el evento pasa a ASSIGNED.
ASSIGN_MOVES_TO_ASSIGNED = {EventState.NEW, EventState.REOPENED}
REASON_REQUIRED = {EventState.REJECTED, EventState.CANCELLED}
CLOSURE_CODE_ALLOWED = {EventState.RESOLVED, EventState.CLOSED}


class EventConflict(Exception):
    """La operación no es válida desde el estado actual del evento (HTTP 409)."""

    code = "conflict"


class InvalidTransition(EventConflict):
    """La transición de estado no está permitida (HTTP 409)."""

    code = "invalid_transition"


class TransitionValidationError(Exception):
    """Datos inválidos en la petición (HTTP 422)."""

    code = "validation_error"

    def __init__(self, fields: dict[str, str]):
        super().__init__("Datos inválidos")
        self.fields = fields


def record_history(
    event,
    *,
    change_type,
    actor_type=ActorType.SYSTEM,
    actor_ref="",
    from_state="",
    to_state="",
    field_name="",
    old_value=None,
    new_value=None,
    description="",
    rule_code="",
    metadata=None,
):
    """Agrega una fila a la bitácora (event_history): quién, cuándo y qué cambió."""
    return EventHistory.objects.create(
        event=event,
        change_type=change_type,
        actor_type=actor_type,
        actor_ref=actor_ref,
        from_state=from_state,
        to_state=to_state,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        description=description,
        rule_code=rule_code,
        metadata=metadata or {},
    )


def allowed_transitions(event) -> list[EventState]:
    """Estados a los que puede pasar el evento, en el orden de EventState."""
    allowed = ALLOWED_TRANSITIONS.get(EventState(event.state), set())
    return [state for state in EventState if state in allowed]


def lock_event(event) -> Event:
    """Relee el evento bloqueando la fila (evita dos cambios simultáneos)."""
    return Event.objects.select_for_update().get(pk=event.pk)


@transaction.atomic
def transition_event(
    event,
    to_state,
    *,
    actor_type=ActorType.USER,
    actor_ref="",
    reason="",
    closure_code="",
    rule_code="",
    description="",
):
    """Cambia el estado si la transición está permitida y deja el historial."""
    try:
        target = EventState(to_state)
    except ValueError:
        raise TransitionValidationError({"to_state": "Estado desconocido"}) from None

    event = lock_event(event)
    current = EventState(event.state)
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"No se puede pasar de {current} a {target}")

    reason = (reason or "").strip()
    if target in REASON_REQUIRED and not reason:
        raise TransitionValidationError({"reason": "Obligatorio al pasar a REJECTED o CANCELLED"})
    if closure_code:
        if closure_code not in ClosureCode.values:
            raise TransitionValidationError({"closure_code": "Valor no válido"})
        if target not in CLOSURE_CODE_ALLOWED:
            raise TransitionValidationError(
                {"closure_code": "Solo aplica al pasar a RESOLVED o CLOSED"}
            )

    now = timezone.now()
    event.state = target
    event.updated_by_ref = actor_ref
    if closure_code:
        event.closure_code = closure_code
    if target == EventState.RESOLVED:
        event.resolved_at = now
    if target in TERMINAL_STATES:  # CLOSED, REJECTED o CANCELLED: fin del evento
        event.closed_at = now
        if not event.closure_code:
            event.closure_code = (
                ClosureCode.SOLVED if target == EventState.CLOSED else ClosureCode.NOT_APPLICABLE
            )
    if target in REASON_REQUIRED:
        event.state_reason = reason
    if target == EventState.REOPENED:
        event.resolved_at = None
        event.closed_at = None
        event.closure_code = ""
    event.save()

    record_history(
        event,
        change_type=ChangeType.STATE_CHANGE,
        actor_type=actor_type,
        actor_ref=actor_ref,
        from_state=current,
        to_state=target,
        description=description or reason,
        rule_code=rule_code,
        metadata={"closure_code": event.closure_code} if event.closure_code else {},
    )
    return event


@transaction.atomic
def assign_event(
    event,
    *,
    assigned_to_ref=None,
    assigned_group_ref=None,
    actor_type=ActorType.USER,
    actor_ref="",
):
    """Asigna usuario y/o grupo. Un evento NEW o REOPENED pasa a ASSIGNED.

    `None` = no cambiar ese campo; `""` = quitarlo. Debe quedar al menos uno.
    """
    event = lock_event(event)
    current = EventState(event.state)
    if current not in ASSIGNABLE_STATES:
        raise EventConflict(f"No se puede asignar un evento en estado {current}")

    new_to = event.assigned_to_ref if assigned_to_ref is None else assigned_to_ref
    new_group = event.assigned_group_ref if assigned_group_ref is None else assigned_group_ref
    if not (new_to or new_group):
        raise TransitionValidationError(
            {"assigned_to_ref": "Indica un usuario o un grupo para asignar"}
        )

    old = {"assigned_to_ref": event.assigned_to_ref, "assigned_group_ref": event.assigned_group_ref}
    new = {"assigned_to_ref": new_to, "assigned_group_ref": new_group}
    if old != new:
        event.assigned_to_ref = new_to
        event.assigned_group_ref = new_group
        event.updated_by_ref = actor_ref
        event.save()
        record_history(
            event,
            change_type=ChangeType.ASSIGNMENT,
            actor_type=actor_type,
            actor_ref=actor_ref,
            field_name="assignment",
            old_value=old,
            new_value=new,
            description="Asignación",
        )

    if current in ASSIGN_MOVES_TO_ASSIGNED:
        event = transition_event(
            event,
            EventState.ASSIGNED,
            actor_type=actor_type,
            actor_ref=actor_ref,
            description="Asignación",
        )
    return event


def should_auto_close(event) -> bool:
    """Regla 1: evento de sistema, informativo y sin acción requerida."""
    return (
        event.state == EventState.NEW
        and event.origin == EventOrigin.SYSTEM
        and event.event_type == EventType.INFORMATION
        and not event.action_required
    )


def auto_close_informational(event):
    """Regla 1: solo registro y cierre automático. Devuelve el evento (cerrado o no)."""
    if not should_auto_close(event):
        return event
    return transition_event(
        event,
        EventState.CLOSED,
        actor_type=ActorType.RULE,
        actor_ref="R1",
        closure_code=ClosureCode.AUTO_LOGGED,
        rule_code="R1",
        description="Regla 1: evento informativo de sistema sin acción; solo registro",
    )
