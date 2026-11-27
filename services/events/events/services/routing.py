"""Adaptación del motor de reglas al registro y al outbox de Eventos."""

from ..models import (
    ChangeType,
    Event,
    EventCategory,
    EventOrigin,
    OutboxMessage,
)
from ..models import (
    EventType as ModelEventType,
)
from ..models.choices import Destination as ModelDestination
from ..outbox import ROUTED, enqueue_routed
from ..rules import (
    Category,
    Destination,
    EventType,
    Origin,
    evaluate,
)
from ..rules import (
    Event as RuleEvent,
)
from .lifecycle import record_history

RULE_TO_MODEL_TYPE = {
    EventType.INFORMATIVE: ModelEventType.INFORMATION,
    EventType.WARNING: ModelEventType.WARNING,
    EventType.EXCEPTION: ModelEventType.EXCEPTION,
}


def security_rule_decision(
    *, origin, event_type, category, action_required, security_exception=False
):
    """Evalúa R4 sin alterar los eventos informativos de Accesos."""
    if category != EventCategory.SECURITY or event_type == ModelEventType.INFORMATION:
        return None
    rule_origin = Origin.SYSTEM if origin == EventOrigin.SYSTEM else Origin.USER
    rule_type = EventType[event_type]
    return evaluate(
        RuleEvent(
            origin=rule_origin,
            event_type=rule_type,
            requires_action=action_required,
            category=Category.SECURITY,
            security_exception=security_exception,
        )
    )


def dispatch_security_event(event: Event, *, security_exception=False) -> None:
    decision = security_rule_decision(
        origin=event.origin,
        event_type=event.event_type,
        category=event.category,
        action_required=event.action_required,
        security_exception=security_exception,
    )
    if decision is None or decision.destination != Destination.ACCESS:
        return

    routed_type = RULE_TO_MODEL_TYPE[decision.event_type]
    if event.event_type != routed_type:
        event.event_type = routed_type
        event.save(update_fields=["event_type", "updated_at"])

    if OutboxMessage.objects.filter(message_type=ROUTED, aggregate_id=event.id).exists():
        return

    enqueue_routed(event, destination=ModelDestination.ACCESS, rule_code="R4")
    record_history(
        event,
        change_type=ChangeType.ROUTING,
        actor_ref="R4",
        rule_code="R4",
        description="Regla 4: evento de seguridad enrutado a Accesos",
        metadata={"destination": ModelDestination.ACCESS, "event_type": routed_type},
    )
