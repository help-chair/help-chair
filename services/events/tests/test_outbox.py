"""Outbox, primera mitad: los mensajes se escriben en la misma transacción que el evento."""

import pytest
from django.db import transaction

from events.models import (
    ActorType,
    BusinessService,
    ClosureCode,
    Event,
    EventState,
    OutboxMessage,
    OutboxStatus,
    ServiceImportance,
)
from events.models.choices import Destination
from events.outbox import ROUTED, STATE_CHANGED, enqueue_routed, envelope
from events.services import register_event, registration, transition_event
from tests.factories import ENVELOPE_SCHEMA, envelope_errors, make_event

pytestmark = pytest.mark.django_db

WARNING = {
    "origin": "SYSTEM",
    "title": "Disco al 85 %",
    "message": "srv-1",
    "payload": {"severity": "warning"},
}
INFO_NO_ACTION = {
    "origin": "SYSTEM",
    "title": "Respaldo terminado",
    "message": "ok",
    "payload": {"severity": "info"},
    "action_required": False,
}


def payloads():
    return [m.payload for m in OutboxMessage.objects.order_by("created_at")]


# --- misma transacción ----------------------------------------------------------------
def test_registering_an_event_writes_a_pending_new_state_message():
    event, _ = register_event(WARNING, actor_ref="user-1")

    message = OutboxMessage.objects.get()
    assert message.status == OutboxStatus.PENDING
    assert message.message_type == STATE_CHANGED
    assert message.subject == "events.state_changed"
    assert message.aggregate_id == event.id
    assert message.attempts == 0
    assert message.payload["from_state"] is None
    assert message.payload["to_state"] == EventState.NEW
    assert message.payload["actor_type"] == ActorType.SYSTEM
    assert message.payload["actor_ref"] == "user-1"


def test_auto_closed_informational_event_writes_new_and_closed_in_order():
    register_event(INFO_NO_ACTION)

    new, closed = payloads()
    assert (new["from_state"], new["to_state"]) == (None, EventState.NEW)
    assert (closed["from_state"], closed["to_state"]) == (EventState.NEW, EventState.CLOSED)
    assert closed["closure_code"] == ClosureCode.AUTO_LOGGED
    assert (closed["actor_type"], closed["actor_ref"]) == (ActorType.RULE, "R1")


def test_a_duplicate_occurrence_does_not_change_state_and_writes_no_message():
    register_event(WARNING)
    _, created = register_event(WARNING)

    assert created is False
    assert OutboxMessage.objects.count() == 1


def test_each_transition_writes_its_message():
    event = make_event()
    transition_event(event, EventState.REJECTED, actor_ref="agent-7", reason="Falso positivo")

    message = OutboxMessage.objects.get()
    assert message.payload["to_state"] == EventState.REJECTED
    assert message.payload["state_reason"] == "Falso positivo"
    assert message.payload["closure_code"] == ClosureCode.NOT_APPLICABLE


def test_the_message_is_rolled_back_together_with_the_event():
    with pytest.raises(RuntimeError), transaction.atomic():
        register_event(WARNING)
        raise RuntimeError("falla después de registrar")

    assert Event.objects.count() == 0
    assert OutboxMessage.objects.count() == 0


def test_the_event_is_not_saved_if_its_message_cannot_be_written(monkeypatch):
    def broken_enqueue(*args, **kwargs):
        raise RuntimeError("no se pudo escribir el outbox")

    monkeypatch.setattr(registration, "enqueue_state_changed", broken_enqueue)
    with pytest.raises(RuntimeError):
        register_event(WARNING)

    assert Event.objects.count() == 0


# --- sobre común y event.routed -------------------------------------------------------
@pytest.mark.skipif(not ENVELOPE_SCHEMA.exists(), reason="contracts/ no está disponible")
def test_state_changed_envelope_conforms_to_the_contract():
    register_event(INFO_NO_ACTION, actor_ref="user-1")

    for message in OutboxMessage.objects.all():
        data = envelope(message)
        assert envelope_errors(data) == []
        assert data["id"] == str(message.id)
        assert data["origin"] == "events"


@pytest.mark.skipif(not ENVELOPE_SCHEMA.exists(), reason="contracts/ no está disponible")
def test_routed_envelope_conforms_to_the_contract():
    service = BusinessService.objects.create(
        code="pagos", name="Pagos", importance=ServiceImportance.CRITICAL
    )
    event = make_event(
        service=service,
        impact="HIGH",
        urgency="HIGH",
        priority="P1",
        payload={"host": "pagos-01", "_ingestion_key": "abc"},
    )

    message = enqueue_routed(event, destination=Destination.INCIDENTS, rule_code="R6")

    assert message.message_type == ROUTED
    assert message.subject == "events.routed.incidents"
    assert message.payload["service_code"] == "pagos"
    assert message.payload["payload"] == {"host": "pagos-01"}  # sin claves internas
    assert envelope_errors(envelope(message)) == []


@pytest.mark.parametrize(
    "destination", [Destination.LOG_ONLY, Destination.EVENTS, Destination.SOLUTION_AUTHOR]
)
def test_routed_is_only_for_other_services(destination):
    with pytest.raises(ValueError):
        enqueue_routed(make_event(), destination=destination, rule_code="R1")
