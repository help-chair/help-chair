"""Plan B: publicación por REST con la misma interfaz y los mismos reintentos del outbox."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.management import CommandError, call_command

from events.models import OutboxMessage, OutboxStatus
from events.outbox import TransientPublishError, get_publisher, publish_pending
from events.outbox.http import HttpPublisher, HttpRejected, parse_routes, subject_matches
from events.outbox.jetstream import JetStreamPublisher
from events.services import register_event
from tests.factories import ENVELOPE_SCHEMA, envelope_errors


class Receiver(ThreadingHTTPServer):
    """Receptor de prueba: guarda cada POST y responde el código configurado por ruta."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), ReceiverHandler)
        self.received = []
        self.status = {}  # ruta -> código HTTP (200 por omisión)

    def url(self, path):
        return f"http://127.0.0.1:{self.server_address[1]}{path}"


class ReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 - nombre que exige BaseHTTPRequestHandler
        length = int(self.headers.get("Content-Length", 0))
        self.server.received.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": json.loads(self.rfile.read(length)),
            }
        )
        self.send_response(self.server.status.get(self.path, 200))
        self.end_headers()

    def log_message(self, *args):  # sin ruido en la salida de pytest
        pass


@pytest.fixture
def receiver():
    server = Receiver()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def register_one():
    register_event({"origin": "SYSTEM", "title": "CPU alta", "message": "srv-1"})
    return OutboxMessage.objects.get()


# --- ruteo ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("pattern", "subject", "expected"),
    [
        ("events.state_changed", "events.state_changed", True),
        ("events.routed.*", "events.routed.incidents", True),
        ("events.routed.*", "events.routed", False),
        ("events.>", "events.routed.incidents", True),
        ("events.>", "events", False),
        ("events.routed.requests", "events.routed.incidents", False),
        ("events.*", "events.routed.incidents", False),
    ],
)
def test_subject_matching_uses_nats_wildcards(pattern, subject, expected):
    assert subject_matches(pattern, subject) is expected


def test_routes_are_parsed_from_the_environment_format():
    routes = parse_routes(
        "events.routed.*=http://a/x, http://b/y ; events.state_changed=http://c/z"
    )

    assert routes == [
        ("events.routed.*", ["http://a/x", "http://b/y"]),
        ("events.state_changed", ["http://c/z"]),
    ]


@pytest.mark.parametrize("raw", ["events.>", "events.>=", "=http://a", "events.>=ftp://a"])
def test_invalid_routes_are_rejected(raw):
    with pytest.raises(ImproperlyConfigured):
        parse_routes(raw)


def test_a_subject_can_fan_out_to_several_receivers_without_repeating_urls():
    publisher = HttpPublisher(
        parse_routes("events.>=http://a/m;events.state_changed=http://a/m,http://b/m"), token=""
    )

    assert publisher.targets_for("events.state_changed") == ["http://a/m", "http://b/m"]
    assert publisher.targets_for("events.routed.incidents") == ["http://a/m"]


# --- entrega --------------------------------------------------------------------------
@pytest.mark.django_db
def test_the_same_envelope_is_posted_with_idempotency_headers(receiver):
    message = register_one()
    routes = parse_routes(f"events.state_changed={receiver.url('/api/incidents/v1/messages')}")

    result = publish_pending(HttpPublisher(routes, token="secreto"))

    assert result.published == 1
    (request,) = receiver.received
    assert request["path"] == "/api/incidents/v1/messages"
    assert request["headers"]["Idempotency-Key"] == str(message.id) == request["body"]["id"]
    assert request["headers"]["X-Message-Subject"] == "events.state_changed"
    assert request["headers"]["Authorization"] == "Bearer secreto"
    if ENVELOPE_SCHEMA.exists():
        assert envelope_errors(request["body"]) == []


@pytest.mark.django_db
@pytest.mark.parametrize("status", [503, 500, 429, 408])
def test_receiver_unavailable_keeps_the_message_pending_and_sends_it_later(receiver, status):
    message = register_one()
    path = "/messages"
    publisher = HttpPublisher(parse_routes(f"events.>={receiver.url(path)}"), token="")
    receiver.status[path] = status

    down = publish_pending(publisher)

    message.refresh_from_db()
    assert down.broker_unavailable
    assert message.status == OutboxStatus.PENDING
    assert f"HTTP {status}" in message.last_error

    receiver.status[path] = 200
    assert publish_pending(publisher).published == 1
    message.refresh_from_db()
    assert message.status == OutboxStatus.PUBLISHED
    # Mismo Idempotency-Key en el reintento: el receptor reconoce el duplicado.
    assert {r["headers"]["Idempotency-Key"] for r in receiver.received} == {str(message.id)}


@pytest.mark.django_db
def test_rejected_message_is_retried_with_backoff_like_any_permanent_failure(receiver):
    message = register_one()
    receiver.status["/messages"] = 422
    publisher = HttpPublisher(parse_routes(f"events.>={receiver.url('/messages')}"), token="")

    result = publish_pending(publisher)

    message.refresh_from_db()
    assert (result.retried, result.broker_unavailable) == (1, False)
    assert message.status == OutboxStatus.PENDING
    assert "HttpRejected" in message.last_error


def test_connection_refused_is_a_transient_failure():
    server = Receiver()  # toma un puerto libre y lo cierra: nadie escucha ahí
    url = server.url("/messages")
    server.server_close()

    with pytest.raises(TransientPublishError):
        HttpPublisher([("events.>", [url])], timeout=2, token="").publish(
            "events.state_changed", b"{}", message_id="m-1"
        )


def test_4xx_raises_http_rejected(receiver):
    receiver.status["/m"] = 400
    publisher = HttpPublisher([("events.>", [receiver.url("/m")])], token="")

    with pytest.raises(HttpRejected):
        publisher.publish("events.state_changed", b"{}", message_id="m-1")


@pytest.mark.django_db
def test_subject_without_routes_counts_as_delivered(receiver):
    register_one()

    result = publish_pending(HttpPublisher(parse_routes("events.routed.*=http://x/m"), token=""))

    assert result.published == 1
    assert receiver.received == []


# --- selección del transporte ---------------------------------------------------------
def test_transport_selects_the_publisher(settings):
    settings.OUTBOX_TRANSPORT = "jetstream"
    settings.BROKER_URL = "nats://broker:4222"
    assert isinstance(get_publisher(), JetStreamPublisher)

    settings.OUTBOX_TRANSPORT = "http"
    settings.OUTBOX_HTTP_ROUTES = "events.>=http://a/m"
    assert isinstance(get_publisher(), HttpPublisher)

    settings.OUTBOX_TRANSPORT = "kafka"
    with pytest.raises(ImproperlyConfigured):
        get_publisher()


@pytest.mark.django_db
def test_command_uses_the_rest_plan_b_without_a_broker(receiver, settings):
    settings.OUTBOX_TRANSPORT = "http"
    settings.BROKER_URL = ""
    settings.OUTBOX_HTTP_ROUTES = f"events.>={receiver.url('/messages')}"
    register_event(
        {
            "origin": "SYSTEM",
            "title": "Respaldo",
            "message": "ok",
            "action_required": False,
            "payload": {"severity": "info"},
        }
    )  # regla 1: NEW + CLOSED

    call_command("publish_outbox")

    assert [r["body"]["payload"]["to_state"] for r in receiver.received] == ["NEW", "CLOSED"]
    assert set(OutboxMessage.objects.values_list("status", flat=True)) == {OutboxStatus.PUBLISHED}


@pytest.mark.django_db
def test_command_rejects_bad_routes(settings):
    settings.OUTBOX_TRANSPORT = "http"
    settings.OUTBOX_HTTP_ROUTES = "events.>=ftp://nope"

    with pytest.raises(CommandError, match="OUTBOX_HTTP_ROUTES"):
        call_command("publish_outbox")
