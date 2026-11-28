"""Consumo idempotente y clasificación de los mensajes contractuales de Accesos."""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from events.models import (
    Event,
    EventCategory,
    EventType,
    OutboxMessage,
    ProcessedAccessMessage,
)
from events.outbox import ROUTED
from events.services.access_ingestion import (
    ACCOUNT_LOCKED,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    PASSWORD_CHANGED,
    InvalidAccessMessage,
    process_access_message,
)
from tests.factories import envelope_errors

pytestmark = pytest.mark.django_db


def access_message(message_type, payload, *, occurred_at=None, message_id=None):
    occurred_at = occurred_at or timezone.now()
    timestamp = occurred_at.isoformat().replace("+00:00", "Z")
    envelope = {
        "id": str(message_id or uuid.uuid4()),
        "type": message_type,
        "version": 1,
        "origin": "access",
        "timestamp": timestamp,
        "occurred_at": timestamp,
        "payload": payload,
    }
    assert envelope_errors(envelope) == []
    return envelope


def failed_login(*, identifier="ana@example.test", ip="192.0.2.10", attempt=1, **kwargs):
    return access_message(
        LOGIN_FAILED,
        {"identificador": identifier, "intentos": attempt, "ip": ip},
        **kwargs,
    )


def routed_messages():
    return list(OutboxMessage.objects.filter(message_type=ROUTED))


def test_successful_login_is_logged_as_informational():
    message = access_message(
        LOGIN_SUCCESS,
        {"usuario_id": "user-1", "rol": "AGENTE_N1", "ip": "192.0.2.10"},
    )

    result = process_access_message(message)

    assert result.event.event_type == EventType.INFORMATION
    assert result.event.category == EventCategory.SECURITY
    assert result.event.payload["usuario_id"] == "user-1"
    assert result.event.state == "CLOSED"
    assert routed_messages() == []


def test_duplicate_envelope_id_is_ignored_without_counting_twice():
    message = failed_login(attempt=4)

    first = process_access_message(message)
    duplicate = process_access_message(message)

    assert first.failure_count == 1
    assert duplicate.duplicate is True
    assert duplicate.event.pk == first.event.pk
    assert ProcessedAccessMessage.objects.count() == 1
    assert Event.objects.count() == 1


def test_fifth_unique_failure_is_warning_and_routes_to_access():
    now = timezone.now()
    results = [
        process_access_message(
            failed_login(
                attempt=attempt,
                occurred_at=now + timedelta(seconds=attempt),
            )
        )
        for attempt in range(1, 6)
    ]

    assert [result.event.event_type for result in results[:4]] == [EventType.INFORMATION] * 4
    assert results[4].failure_count == 5
    assert results[4].event.event_type == EventType.WARNING
    assert results[4].event.category == EventCategory.SECURITY

    routed = routed_messages()
    assert len(routed) == 1
    assert routed[0].payload["destination"] == "ACCESS"
    assert routed[0].payload["rule_code"] == "R4"
    assert routed[0].payload["event_type"] == EventType.WARNING


def test_failure_threshold_is_scoped_to_identifier_and_ip():
    now = timezone.now()
    first_group = [
        process_access_message(
            failed_login(attempt=index, occurred_at=now + timedelta(seconds=index))
        )
        for index in range(1, 5)
    ]
    other_ip = process_access_message(
        failed_login(ip="192.0.2.11", occurred_at=now + timedelta(seconds=4))
    )
    other_identifier = process_access_message(
        failed_login(identifier="another@example.test", occurred_at=now + timedelta(seconds=4))
    )
    fifth = process_access_message(failed_login(attempt=5, occurred_at=now + timedelta(seconds=5)))

    assert [result.event.event_type for result in first_group] == [EventType.INFORMATION] * 4
    assert other_ip.failure_count == 1
    assert other_ip.event.event_type == EventType.INFORMATION
    assert other_identifier.failure_count == 1
    assert other_identifier.event.event_type == EventType.INFORMATION
    assert fifth.failure_count == 5
    assert fifth.event.event_type == EventType.WARNING


def test_old_failures_outside_the_window_do_not_reach_threshold():
    now = timezone.now()
    process_access_message(failed_login(attempt=1, occurred_at=now - timedelta(seconds=301)))

    current = process_access_message(failed_login(attempt=5, occurred_at=now))

    assert current.failure_count == 1
    assert current.event.event_type == EventType.INFORMATION


@pytest.mark.parametrize(
    ("message_type", "payload"),
    [
        (
            ACCOUNT_LOCKED,
            {"usuario_id": "user-1", "intentos": 5, "desbloquea_en": None},
        ),
        (PASSWORD_CHANGED, {"usuario_id": "user-1", "forzado": True}),
    ],
)
def test_security_exceptions_are_routed_to_access(message_type, payload):
    result = process_access_message(access_message(message_type, payload))

    assert result.event.event_type == EventType.EXCEPTION
    assert result.event.category == EventCategory.SECURITY
    routed = routed_messages()
    assert len(routed) == 1
    assert routed[0].payload["destination"] == "ACCESS"
    assert routed[0].payload["rule_code"] == "R4"
    assert routed[0].payload["event_type"] == EventType.EXCEPTION


def test_non_forced_password_change_remains_informational():
    result = process_access_message(
        access_message(PASSWORD_CHANGED, {"usuario_id": "user-1", "forzado": False})
    )

    assert result.event.event_type == EventType.INFORMATION
    assert routed_messages() == []


def test_invalid_access_envelope_is_rejected():
    message = access_message(
        LOGIN_SUCCESS,
        {"usuario_id": "user-1", "rol": "AGENTE_N1", "ip": None},
    )
    message["origin"] = "events"

    with pytest.raises(InvalidAccessMessage, match="origin"):
        process_access_message(message)

    assert ProcessedAccessMessage.objects.count() == 0
