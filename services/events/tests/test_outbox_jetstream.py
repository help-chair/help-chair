"""Integración con un NATS JetStream real (se salta si no hay broker).

    docker run --rm -p 4222:4222 docker.io/library/nats:2-alpine -js
    NATS_TEST_URL=nats://127.0.0.1:4222 uv run pytest tests/test_outbox_jetstream.py

Usa un stream propio (`EVENTS_TEST`) y lo borra al terminar. El broker debe ser desechable: el
stream de prueba toma los subjects `events.>`, que chocan con un stream EVENTS ya existente.
"""

import asyncio
import json
import os

import pytest
from django.core.management import call_command

from events.models import OutboxMessage, OutboxStatus
from events.outbox.jetstream import STREAM_SUBJECTS, JetStreamPublisher
from events.services import register_event
from tests.factories import ENVELOPE_SCHEMA, envelope_errors

NATS_URL = os.environ.get("NATS_TEST_URL", "")
STREAM = "EVENTS_TEST"

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.skipif(not NATS_URL, reason="NATS_TEST_URL no está definido (sin broker real)"),
]


async def _quiet(_error):
    pass


async def _with_js(action):
    import nats

    # Reintentos cortos: el proxy de puertos de Docker Desktop (Windows) a veces corta la
    # conexión antes del INFO de NATS cuando se abren muchas seguidas.
    nc = await nats.connect(
        servers=[NATS_URL], max_reconnect_attempts=5, reconnect_time_wait=0.2, error_cb=_quiet
    )
    try:
        return await action(nc.jetstream())
    finally:
        await nc.close()


def delete_stream():
    from nats.js.errors import NotFoundError

    async def action(js):
        try:
            await js.delete_stream(STREAM)
        except NotFoundError:
            pass

    asyncio.run(_with_js(action))


def stream_messages():
    """(cabeceras, cuerpo) de cada mensaje guardado en el stream, en orden."""

    async def action(js):
        info = await js.stream_info(STREAM)
        messages = []
        for seq in range(info.state.first_seq, info.state.last_seq + 1):
            raw = await js.get_msg(STREAM, seq)
            messages.append((raw.headers or {}, json.loads(raw.data)))
        return messages

    return asyncio.run(_with_js(action))


@pytest.fixture(autouse=True)
def isolated_stream(settings):
    settings.OUTBOX_STREAM = STREAM
    delete_stream()
    yield
    delete_stream()


def test_publisher_creates_the_stream_and_jetstream_stores_the_message():
    with JetStreamPublisher(NATS_URL) as publisher:
        publisher.publish("events.state_changed", b'{"id": "1"}', message_id="m-1")

    ((headers, body),) = stream_messages()
    assert headers["Nats-Msg-Id"] == "m-1"
    assert body == {"id": "1"}


def test_same_message_id_is_stored_once():
    with JetStreamPublisher(NATS_URL) as publisher:
        publisher.publish("events.state_changed", b"{}", message_id="m-dup")
        publisher.publish("events.state_changed", b"{}", message_id="m-dup")  # reintento

    assert len(stream_messages()) == 1


def test_stream_covers_the_events_subjects():
    with JetStreamPublisher(NATS_URL):
        pass

    async def action(js):
        return (await js.stream_info(STREAM)).config.subjects

    assert asyncio.run(_with_js(action)) == list(STREAM_SUBJECTS)


def test_command_publishes_registered_events_end_to_end():
    register_event(
        {
            "origin": "SYSTEM",
            "title": "Respaldo ok",
            "message": "ok",
            "action_required": False,
            "payload": {"severity": "info"},
        }
    )  # regla 1: NEW + CLOSED

    call_command("publish_outbox", url=NATS_URL)

    assert set(OutboxMessage.objects.values_list("status", flat=True)) == {OutboxStatus.PUBLISHED}
    stored = stream_messages()
    assert [body["payload"]["to_state"] for _, body in stored] == ["NEW", "CLOSED"]
    ids = [
        str(i) for i in OutboxMessage.objects.order_by("created_at").values_list("id", flat=True)
    ]
    assert [headers["Nats-Msg-Id"] for headers, _ in stored] == ids
    if ENVELOPE_SCHEMA.exists():
        assert all(envelope_errors(body) == [] for _, body in stored)
