"""Entrega real contra podman compose. Requiere INTEGRATION=1 y un JWT de servicio."""

import os

import httpx
import pytest

from events.models import EventCategory, EventType, RoutingStatus
from events.services import dispatch
from tests.factories import make_event

pytestmark = [
    pytest.mark.integration,
    pytest.mark.django_db,
    pytest.mark.skipif(not os.environ.get("INTEGRATION"), reason="Usa INTEGRATION=1 y make up"),
]

HOSTS = {
    "INCIDENTS": ("http://localhost:8004", "/api/incidents/v1/incidents/{id}/"),
    "PROBLEMS": ("http://localhost:8005", "/api/problems/v1/problemas/{id}/"),
}


@pytest.fixture(autouse=True)
def real_services(settings, monkeypatch):
    settings.DESTINATION_URLS = {k: v[0] for k, v in HOSTS.items()} | {
        "ACCESS": "http://localhost:8002"
    }
    settings.SERVICE_JWT = os.environ.get("SERVICE_JWT", "")
    settings.SERVICE_ACCOUNT_EMAIL = os.environ.get("SERVICE_ACCOUNT_EMAIL", "")
    settings.SERVICE_ACCOUNT_PASSWORD = os.environ.get("SERVICE_ACCOUNT_PASSWORD", "")
    monkeypatch.setattr("events.clients.destinations._token_provider", None)


@pytest.mark.parametrize(
    "overrides, destination",
    [
        (
            {
                "event_type": EventType.EXCEPTION,
                "category": EventCategory.FAILURE,
                "impact": "HIGH",
                "urgency": "HIGH",
            },
            "INCIDENTS",
        ),
        ({"event_type": EventType.WARNING, "occurrence_count": 3}, "PROBLEMS"),
    ],
)
def test_event_is_created_in_the_remote_service(overrides, destination):
    event = make_event(**overrides)
    routing = dispatch.dispatch_event(event.pk)

    assert routing.status == RoutingStatus.SENT, routing.last_error
    host, path = HOSTS[destination]
    token = dispatch.get_client(destination).tokens.get_token()
    resp = httpx.get(
        host + path.format(id=routing.remote_id), headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
