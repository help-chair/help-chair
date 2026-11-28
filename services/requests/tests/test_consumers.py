import asyncio
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from peticiones.consumers import (
    DEFAULT_SERVICE_NAME,
    SYSTEM_REQUESTER_ID,
    InvalidEventError,
    process_routed_event,
)
from peticiones.management.commands.consume_events import handle_raw_message
from peticiones.models import CatalogItem, ServiceRequest


def _build_envelope(
    *,
    event_id: str = "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    destination: str = "REQUESTS",
    category: str = "REQUEST",
    service_code: str | None = None,
    title: str = "Solicitud de acceso a repositorio",
    message: str = "Alta de permisos solicitada.",
    reporter_ref: str | None = "42",
    raw_payload: dict | None = None,
) -> dict:
    return {
        "id": "0b9d6b1e-6c0a-4f0e-9d7e-3a1f1f7b2c11",
        "type": "event.routed",
        "version": 1,
        "origin": "events",
        "timestamp": "2026-11-22T10:00:01Z",
        "occurred_at": "2026-11-22T10:00:00Z",
        "payload": {
            "event_id": event_id,
            "destination": destination,
            "rule_code": "R5",
            "event_type": "INFORMATION",
            "category": category,
            "state": "NEW",
            "title": title,
            "message": message,
            "action_required": True,
            "occurrence_count": 1,
            "fingerprint": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "first_seen_at": "2026-11-22T10:00:00Z",
            "last_seen_at": "2026-11-22T10:00:00Z",
            "service_code": service_code,
            "reporter_ref": reporter_ref,
            "payload": raw_payload or {"repo": "help-chair"},
        },
    }


@pytest.mark.django_db
def test_process_routed_event_creates_request_with_matching_service():
    catalog_item = CatalogItem.objects.create(name="Soporte Técnico")
    envelope = _build_envelope(
        service_code="soporte técnico",
        reporter_ref="42",
    )

    service_request, created = process_routed_event(envelope)

    assert created is True
    assert service_request is not None
    assert service_request.event_id == "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    assert service_request.service == catalog_item
    assert service_request.requester_id == "42"
    assert service_request.status == ServiceRequest.Status.NEW
    assert service_request.approval_status == ServiceRequest.ApprovalStatus.NOT_REQUIRED


@pytest.mark.django_db
def test_process_routed_change_event_requires_approval():
    envelope = _build_envelope(
        event_id="11111111-2222-3333-4444-555555555555",
        category="CHANGE",
        reporter_ref=None,
    )

    service_request, created = process_routed_event(envelope)

    assert created is True
    assert service_request is not None
    assert service_request.request_type == ServiceRequest.RequestType.CHANGE
    assert service_request.approval_status == ServiceRequest.ApprovalStatus.PENDING
    assert service_request.requester_id == SYSTEM_REQUESTER_ID
    assert service_request.service.name == DEFAULT_SERVICE_NAME


@pytest.mark.django_db
def test_process_routed_event_ignores_other_destinations():
    envelope = _build_envelope(destination="INCIDENTS")

    service_request, created = process_routed_event(envelope)

    assert service_request is None
    assert created is False
    assert ServiceRequest.objects.count() == 0


@pytest.mark.django_db
def test_process_routed_event_is_idempotent():
    envelope = _build_envelope(event_id="99999999-aaaa-bbbb-cccc-dddddddddddd")

    first, created_1 = process_routed_event(envelope)
    second, created_2 = process_routed_event(envelope)

    assert created_1 is True
    assert created_2 is False
    assert first is not None and second is not None
    assert first.id == second.id
    assert (
        ServiceRequest.objects.filter(event_id="99999999-aaaa-bbbb-cccc-dddddddddddd").count() == 1
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_envelope",
    [
        "no-es-un-dict",
        {},
        {"type": "event.state_changed", "payload": {}},
        {"type": "event.routed", "payload": "no-dict"},
        {"type": "event.routed", "payload": {"destination": "REQUESTS"}},
    ],
)
def test_process_routed_event_rejects_invalid_envelopes(invalid_envelope):
    with pytest.raises(InvalidEventError):
        process_routed_event(invalid_envelope)


@pytest.mark.django_db(transaction=True)
def test_handle_raw_message_ignores_noise_and_processes_valid():
    asyncio.run(handle_raw_message(b"{json-corrupto"))
    asyncio.run(handle_raw_message(json.dumps({"invalid": True}).encode("utf-8")))
    assert ServiceRequest.objects.count() == 0

    valid_bytes = json.dumps(
        _build_envelope(event_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    ).encode("utf-8")
    asyncio.run(handle_raw_message(valid_bytes))
    assert (
        ServiceRequest.objects.filter(event_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee").count() == 1
    )


def test_consume_events_fails_without_broker_url(settings):
    settings.BROKER_URL = ""
    with pytest.raises(CommandError, match="BROKER_URL"):
        call_command("consume_events")
