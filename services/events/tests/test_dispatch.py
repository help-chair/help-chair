import pytest
from django.core.management import call_command

from events.clients import DestinationError, RemoteResult
from events.models import (
    ChangeType,
    EventCategory,
    EventHistory,
    EventRouting,
    EventState,
    EventType,
    RoutingStatus,
)
from events.services import dispatch, register_event
from tests.factories import make_event

pytestmark = pytest.mark.django_db


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def create(self, event, *, rule_code):
        self.calls.append((event.pk, rule_code))
        if self.error:
            raise self.error
        return RemoteResult(remote_id="42")


@pytest.fixture
def fake(monkeypatch):
    clients = {}

    def factory(destination):
        return clients.setdefault(destination, FakeClient())

    monkeypatch.setattr(dispatch, "get_client", factory)
    factory.clients = clients
    return factory


@pytest.mark.parametrize(
    "overrides, destination, rule",
    [
        ({"event_type": EventType.EXCEPTION, "category": EventCategory.SECURITY}, "ACCESS", "R4"),
        ({"category": EventCategory.REQUEST}, "REQUESTS", "R5"),
        ({"event_type": EventType.EXCEPTION, "category": EventCategory.FAILURE}, "INCIDENTS", "R6"),
        ({"event_type": EventType.WARNING, "occurrence_count": 3}, "PROBLEMS", "R7"),
        ({"category": EventCategory.CHANGE}, "REQUESTS", "R8"),
    ],
)
def test_rules_4_to_8_deliver_and_store_remote_id(fake, overrides, destination, rule):
    event = make_event(**overrides)
    routing = dispatch.dispatch_event(event.pk)

    assert (routing.destination, routing.rule_code) == (destination, rule)
    assert routing.status == RoutingStatus.SENT
    assert routing.remote_id == "42"
    assert EventHistory.objects.filter(event=event, change_type=ChangeType.ROUTING).count() == 1


def test_rule_3_is_not_routed(fake):
    event = make_event(event_type=EventType.WARNING)  # 1 ocurrencia < umbral 3
    assert dispatch.dispatch_event(event.pk) is None
    assert not EventRouting.objects.exists()


def test_rule_9_goes_to_incidents_as_manual_triage(fake):
    event = make_event(event_type=EventType.EXCEPTION)
    routing = dispatch.dispatch_event(event.pk)
    assert (routing.destination, routing.rule_code) == ("INCIDENTS", "R9")
    assert routing.status == RoutingStatus.SENT


def test_retryable_failure_leaves_event_pending_with_reason(fake):
    fake(dispatch.Destination.INCIDENTS).error = DestinationError("HTTP 503", retryable=True)
    event = make_event(event_type=EventType.EXCEPTION, category=EventCategory.FAILURE)

    routing = dispatch.dispatch_event(event.pk)

    assert routing.status == RoutingStatus.PENDING
    assert "503" in routing.last_error and routing.attempts == 1
    event.refresh_from_db()
    assert event.state == EventState.NEW


def test_non_retryable_failure_goes_to_triage(fake):
    fake(dispatch.Destination.INCIDENTS).error = DestinationError("HTTP 400", retryable=False)
    event = make_event(event_type=EventType.EXCEPTION, category=EventCategory.FAILURE)
    assert dispatch.dispatch_event(event.pk).status == RoutingStatus.TRIAGE


def test_gives_up_after_max_attempts(fake, settings):
    settings.ROUTING_RETRY_DELAY = 0
    settings.ROUTING_MAX_ATTEMPTS = 2
    fake(dispatch.Destination.INCIDENTS).error = DestinationError("timeout", retryable=True)
    event = make_event(event_type=EventType.EXCEPTION, category=EventCategory.FAILURE)

    assert dispatch.dispatch_event(event.pk).status == RoutingStatus.PENDING
    assert dispatch.retry_pending() == 1
    assert EventRouting.objects.get().status == RoutingStatus.TRIAGE


def test_retry_pending_delivers_once_destination_recovers(fake, settings):
    settings.ROUTING_RETRY_DELAY = 0
    client = fake(dispatch.Destination.PROBLEMS)
    client.error = DestinationError("caído", retryable=True)
    event = make_event(event_type=EventType.WARNING, occurrence_count=3)
    dispatch.dispatch_event(event.pk)

    client.error = None
    dispatch.retry_pending()

    routing = EventRouting.objects.get()
    assert routing.status == RoutingStatus.SENT and routing.remote_id == "42"


def test_second_dispatch_does_not_resend(fake):
    event = make_event(event_type=EventType.EXCEPTION, category=EventCategory.FAILURE)
    dispatch.dispatch_event(event.pk)
    dispatch.dispatch_event(event.pk)
    assert len(fake(dispatch.Destination.INCIDENTS).calls) == 1


def test_register_event_dispatches_after_commit(fake, django_capture_on_commit_callbacks, settings):
    settings.ROUTING_DISPATCH_MODE = "inline"
    data = {
        "origin": "SYSTEM",
        "title": "Pagos caído",
        "message": "timeout",
        "event_type": "EXCEPTION",
        "category": "FAILURE",
    }
    with django_capture_on_commit_callbacks(execute=True):
        event, created = register_event(data)

    assert created
    assert EventRouting.objects.get(event=event).status == RoutingStatus.SENT


def test_threshold_crossing_routes_a_repeated_warning_to_problems(
    fake, django_capture_on_commit_callbacks, settings
):
    settings.ROUTING_DISPATCH_MODE = "inline"
    data = {"origin": "SYSTEM", "title": "Disco", "message": "85 %", "event_type": "WARNING"}
    for _ in range(3):  # umbral por defecto: 3
        with django_capture_on_commit_callbacks(execute=True):
            event, _created = register_event(data)

    routing = EventRouting.objects.get(event=event)
    assert (routing.destination, routing.rule_code) == ("PROBLEMS", "R7")


def test_deferred_mode_creates_pending_routing_in_the_same_transaction(fake, settings):
    settings.ROUTING_DISPATCH_MODE = "deferred"
    event, _ = register_event(
        {
            "origin": "SYSTEM",
            "title": "Pagos",
            "message": "x",
            "event_type": "EXCEPTION",
            "category": "FAILURE",
        }
    )
    routing = EventRouting.objects.get(event=event)
    assert routing.status == RoutingStatus.PENDING and routing.attempts == 0
    assert fake.clients == {}  # todavía no se llamó a ningún servicio

    dispatch.retry_pending()
    routing.refresh_from_db()
    assert routing.status == RoutingStatus.SENT and routing.remote_id == "42"


def test_retry_routing_command_runs_once(fake, settings, capsys):
    settings.ROUTING_RETRY_DELAY = 0
    make_event(event_type=EventType.EXCEPTION, category=EventCategory.FAILURE)
    dispatch.dispatch_event(
        make_event(event_type=EventType.EXCEPTION, category=EventCategory.FAILURE).pk,
        send=False,
    )
    call_command("retry_routing")
    assert "Reintentadas: 1" in capsys.readouterr().out
