"""Entrega los eventos al servicio que decidió el motor de reglas (reglas 4 a 9)."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from .. import rules
from ..clients import DestinationError, get_client
from ..models import (
    TERMINAL_STATES,
    ActorType,
    ChangeType,
    Destination,
    Event,
    EventOrigin,
    EventRouting,
    RoutingStatus,
)
from .classification import resolve_recurrence
from .lifecycle import record_history

logger = logging.getLogger(__name__)

EVENT_TYPE = {
    "INFORMATION": rules.EventType.INFORMATIVE,
    "WARNING": rules.EventType.WARNING,
    "EXCEPTION": rules.EventType.EXCEPTION,
}
CATEGORY = {
    "SECURITY": rules.Category.SECURITY,
    "REQUEST": rules.Category.CATALOG_REQUEST,
    "FAILURE": rules.Category.FAILURE,
    "CHANGE": rules.Category.CHANGE,
}  # GENERAL no tiene equivalente en el motor: llega como None
# Destinos del motor que salen a otro servicio.
# Regla 8 (CHANGE) -> Peticiones; regla 9 (MANUAL_TRIAGE) -> Incidencias.
ROUTABLE = {
    rules.Destination.ACCESS: Destination.ACCESS,
    rules.Destination.REQUEST: Destination.REQUESTS,
    rules.Destination.CHANGE: Destination.REQUESTS,
    rules.Destination.INCIDENT: Destination.INCIDENTS,
    rules.Destination.PROBLEM: Destination.PROBLEMS,
    rules.Destination.MANUAL_TRIAGE: Destination.INCIDENTS,
}


def to_rule_event(event) -> rules.Event:
    return rules.Event(
        origin=rules.Origin.USER if event.origin == EventOrigin.USER else rules.Origin.SYSTEM,
        event_type=EVENT_TYPE[event.event_type],
        requires_action=event.action_required,
        category=CATEGORY.get(event.category),
        repetitions=event.occurrence_count,
        threshold=resolve_recurrence(event).threshold_count,
    )


def dispatch_event(event_id, *, send=True):
    """Evalúa las reglas y registra (y, si send=True, entrega) el envío."""
    try:
        event = Event.objects.select_related("service").get(pk=event_id)
    except Event.DoesNotExist:
        return None
    if event.state in TERMINAL_STATES:
        return None
    decision = rules.evaluate(to_rule_event(event))
    destination = ROUTABLE.get(decision.destination)
    if destination is None:  # reglas 1, 2 y 3: se resuelven dentro de Eventos
        return None
    routing, _ = EventRouting.objects.get_or_create(
        event=event, destination=destination, defaults={"rule_code": f"R{decision.rule}"}
    )
    if routing.status != RoutingStatus.PENDING or not send:
        return routing
    return deliver(routing)


def deliver(routing, *, client=None):
    """Un intento de entrega. Deja SENT, PENDING o TRIAGE con el motivo."""
    event = routing.event
    client = client or get_client(routing.destination)
    routing.attempts += 1
    routing.last_attempt_at = timezone.now()
    try:
        result = client.create(event, rule_code=routing.rule_code)
    except DestinationError as exc:
        give_up = not exc.retryable or routing.attempts >= settings.ROUTING_MAX_ATTEMPTS
        routing.status = RoutingStatus.TRIAGE if give_up else RoutingStatus.PENDING
        routing.last_error = str(exc)[:500]
        description = (
            f"{routing.rule_code}: no se pudo entregar a {routing.destination} "
            f"({routing.status}): {routing.last_error}"
        )
        metadata = {
            "destination": routing.destination,
            "status": routing.status,
            "attempts": routing.attempts,
            "error": routing.last_error,
        }
        logger.warning("event_routing_failed", extra={"event_id": str(event.pk), **metadata})
    else:
        routing.status = RoutingStatus.SENT
        routing.remote_id = result.remote_id
        routing.sent_at = routing.last_attempt_at
        routing.last_error = ""
        description = (
            f"{routing.rule_code}: entregado a {routing.destination} (ID remoto {result.remote_id})"
        )
        metadata = {
            "destination": routing.destination,
            "status": "SENT",
            "remote_id": result.remote_id,
            "attempts": routing.attempts,
        }
    with transaction.atomic():
        routing.save()
        record_history(
            event,
            change_type=ChangeType.ROUTING,
            actor_type=ActorType.RULE,
            actor_ref=routing.rule_code,
            description=description,
            rule_code=routing.rule_code,
            metadata=metadata,
        )
    return routing


def retry_pending(limit=50) -> int:
    """Entrega las PENDING que ya cumplieron la espera. Seguro con varios workers."""
    cutoff = timezone.now() - timedelta(seconds=settings.ROUTING_RETRY_DELAY)
    ids = list(
        EventRouting.objects.filter(status=RoutingStatus.PENDING)
        .filter(Q(last_attempt_at__isnull=True) | Q(last_attempt_at__lte=cutoff))
        .exclude(event__state__in=TERMINAL_STATES)
        .order_by(F("last_attempt_at").asc(nulls_first=True), "id")
        .values_list("pk", flat=True)[:limit]
    )
    count = 0
    for pk in ids:
        with transaction.atomic():
            routing = (
                EventRouting.objects.select_for_update(skip_locked=True, of=("self",))
                .select_related("event", "event__service")
                .filter(pk=pk, status=RoutingStatus.PENDING)
                .first()
            )
            if routing is None:  # otro worker la tomó
                continue
            deliver(routing)
            count += 1
    return count


def schedule_dispatch(event_id):
    """Punto de enganche desde registration.py. Depende de ROUTING_DISPATCH_MODE.

    - deferred (por defecto): crea el envío PENDING dentro de la transacción del evento
      (outbox); lo entrega `manage.py retry_routing --loop`.
    - inline: entrega después del commit, bloqueando la petición. Solo para depurar.
    - off: no enruta.
    """
    mode = getattr(settings, "ROUTING_DISPATCH_MODE", "deferred")
    if mode == "off":
        return
    if mode == "deferred":
        try:
            dispatch_event(event_id, send=False)
        except Exception:  # un fallo de enrutamiento nunca debe tumbar el registro
            logger.exception("event_dispatch_failed", extra={"event_id": str(event_id)})
        return

    def run():
        try:
            dispatch_event(event_id, send=True)
        except Exception:
            logger.exception("event_dispatch_failed", extra={"event_id": str(event_id)})

    transaction.on_commit(run)
