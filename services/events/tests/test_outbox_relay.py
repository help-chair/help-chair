"""Outbox, segunda mitad: publicación con reintentos, broker caído y comando publish_outbox."""

import json
import threading
from contextlib import contextmanager
from datetime import timedelta

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from events.management.commands import publish_outbox
from events.models import OutboxMessage, OutboxStatus
from events.outbox import TransientPublishError, drain, publish_pending
from events.outbox.jetstream import BrokerUnavailable
from events.outbox.relay import backoff_seconds
from events.services import register_event
from tests.factories import ENVELOPE_SCHEMA, envelope_errors

pytestmark = pytest.mark.django_db


class FakePublisher:
    """Publicador en memoria. `fail` es una excepción que se lanza en cada publicación."""

    def __init__(self, fail=None):
        self.fail = fail
        self.sent = []

    def publish(self, subject, body, *, message_id):
        if self.fail is not None:
            raise self.fail
        self.sent.append({"subject": subject, "body": json.loads(body), "message_id": message_id})

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None


def register(n):
    for i in range(n):
        register_event({"origin": "SYSTEM", "title": f"Alerta {i}", "message": "m"})
    return list(OutboxMessage.objects.order_by("created_at"))


def statuses():
    return list(OutboxMessage.objects.order_by("created_at").values_list("status", flat=True))


# --- publicación ----------------------------------------------------------------------
def test_pending_messages_are_published_with_the_contract_envelope():
    (message,) = register(1)
    publisher = FakePublisher()

    result = publish_pending(publisher)

    assert result.published == 1
    message.refresh_from_db()
    assert message.status == OutboxStatus.PUBLISHED
    assert message.published_at is not None
    assert message.attempts == 1
    (sent,) = publisher.sent
    assert sent["subject"] == "events.state_changed"
    assert sent["message_id"] == str(message.id) == sent["body"]["id"]
    if ENVELOPE_SCHEMA.exists():
        assert envelope_errors(sent["body"]) == []


def test_published_messages_are_not_sent_again():
    register(1)
    publish_pending(FakePublisher())
    publisher = FakePublisher()

    assert publish_pending(publisher).published == 0
    assert publisher.sent == []


# --- broker no disponible ---------------------------------------------------------------
def test_broker_down_keeps_messages_pending_and_sends_them_later_in_order():
    messages = register(3)

    down = publish_pending(FakePublisher(fail=TransientPublishError("connection refused")))

    assert down.broker_unavailable and down.published == 0
    assert statuses() == [OutboxStatus.PENDING] * 3
    first = OutboxMessage.objects.get(pk=messages[0].pk)
    assert first.attempts == 1
    assert "connection refused" in first.last_error
    assert first.next_attempt_at <= timezone.now()  # sigue vencido: sale primero al volver

    publisher = FakePublisher()
    up = publish_pending(publisher)

    assert up.published == 3
    assert statuses() == [OutboxStatus.PUBLISHED] * 3
    assert [s["message_id"] for s in publisher.sent] == [str(m.id) for m in messages]


def test_a_long_outage_never_marks_messages_as_failed():
    register(1)
    for _ in range(20):
        publish_pending(FakePublisher(fail=TransientPublishError("timeout")), max_attempts=3)

    message = OutboxMessage.objects.get()
    assert message.status == OutboxStatus.PENDING
    assert message.attempts == 20


def test_unreachable_broker_raises_command_error_and_keeps_messages(settings):
    settings.OUTBOX_PUBLISH_TIMEOUT_SECONDS = 1
    register(2)

    with pytest.raises(CommandError, match="PENDING"):
        call_command(
            "publish_outbox", url="nats://127.0.0.1:1"
        )  # puerto cerrado: broker real caído

    assert statuses() == [OutboxStatus.PENDING] * 2


# --- fallas permanentes y reintentos ------------------------------------------------------
def test_a_bad_message_is_rescheduled_without_blocking_the_rest():
    bad, good = register(2)

    class RejectsFirst(FakePublisher):
        def publish(self, subject, body, *, message_id):
            if message_id == str(bad.id):
                raise ValueError("mensaje demasiado grande")
            super().publish(subject, body, message_id=message_id)

    now = timezone.now()
    result = publish_pending(RejectsFirst(), now=now)

    assert (result.published, result.retried) == (1, 1)
    bad.refresh_from_db()
    assert bad.status == OutboxStatus.PENDING
    assert bad.next_attempt_at == now + timedelta(seconds=backoff_seconds(1))
    assert "ValueError: mensaje demasiado grande" in bad.last_error
    good.refresh_from_db()
    assert good.status == OutboxStatus.PUBLISHED


def test_rescheduled_message_waits_until_its_next_attempt():
    (message,) = register(1)
    now = timezone.now()
    publish_pending(FakePublisher(fail=ValueError("x")), now=now)
    message.refresh_from_db()

    early = FakePublisher()
    publish_pending(early, now=message.next_attempt_at - timedelta(seconds=1))
    assert early.sent == []

    on_time = FakePublisher()
    publish_pending(on_time, now=message.next_attempt_at)
    assert len(on_time.sent) == 1


def test_after_max_attempts_the_message_is_failed():
    (message,) = register(1)
    now = timezone.now()
    for attempt in range(3):
        result = publish_pending(
            FakePublisher(fail=ValueError("x")), max_attempts=3, now=now + timedelta(days=attempt)
        )

    assert result.failed == 1
    message.refresh_from_db()
    assert message.status == OutboxStatus.FAILED
    assert message.attempts == 3
    assert publish_pending(FakePublisher(), now=now + timedelta(days=9)).published == 0


def test_backoff_doubles_until_the_cap(settings):
    settings.OUTBOX_BACKOFF_BASE_SECONDS = 5
    settings.OUTBOX_BACKOFF_MAX_SECONDS = 60

    assert [backoff_seconds(n) for n in range(1, 7)] == [5, 10, 20, 40, 60, 60]


def test_drain_publishes_in_batches_until_nothing_is_due():
    register(5)
    publisher = FakePublisher()

    result = drain(publisher, batch_size=2)

    assert result.published == 5
    assert len(publisher.sent) == 5


# --- comando --------------------------------------------------------------------------
def use_publisher(monkeypatch, factory):
    monkeypatch.setattr(publish_outbox, "get_publisher", lambda url: factory())


def test_command_requires_a_broker_url(settings):
    settings.BROKER_URL = ""
    with pytest.raises(CommandError, match="BROKER_URL"):
        call_command("publish_outbox")


def test_command_publishes_pending_messages(monkeypatch, settings, capsys):
    settings.BROKER_URL = "nats://broker:4222"
    register(2)
    publisher = FakePublisher()
    use_publisher(monkeypatch, lambda: publisher)

    call_command("publish_outbox")

    assert len(publisher.sent) == 2
    assert statuses() == [OutboxStatus.PUBLISHED] * 2
    assert "Publicados: 2" in capsys.readouterr().out


def test_worker_reconnects_after_the_broker_comes_back(monkeypatch, settings):
    settings.BROKER_URL = "nats://broker:4222"
    register(1)
    publisher = FakePublisher()
    connections = iter([BrokerUnavailable("caído"), publisher])

    @contextmanager
    def flaky_publisher():
        item = next(connections)
        if isinstance(item, Exception):
            raise item
        yield item

    class StopOnSecondWait(threading.Event):
        waits = 0

        def wait(self, timeout=None):
            StopOnSecondWait.waits += 1
            if StopOnSecondWait.waits >= 2:
                self.set()
            return self.is_set()

    use_publisher(monkeypatch, flaky_publisher)
    monkeypatch.setattr(publish_outbox.threading, "Event", StopOnSecondWait)
    monkeypatch.setattr(publish_outbox.signal, "signal", lambda *args: None)

    call_command("publish_outbox", loop=True, interval=0.01)

    assert len(publisher.sent) == 1
    assert statuses() == [OutboxStatus.PUBLISHED]
