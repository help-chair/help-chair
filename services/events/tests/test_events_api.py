from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from events.models import (
    BusinessService,
    Event,
    EventState,
    PriorityMatrix,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def service(db):
    return BusinessService.objects.create(
        code="pagos",
        name="Pasarela de pagos",
        importance="HIGH",
        is_active=True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("origin", ["USER", "SYSTEM"])
def test_create_event(api_client, origin, service):
    occurred_at = timezone.now() - timedelta(minutes=5)
    response = api_client.post(
        "/api/v1/events",
        {
            "origin": origin,
            "title": "Timeout en pagos",
            "message": "El servicio no responde",
            "service_code": service.code,
            "payload": {"host": "pagos-01"},
            "occurred_at": occurred_at.isoformat(),
        },
        format="json",
    )

    assert response.status_code == 201
    assert response["Location"].startswith("/api/v1/events/")
    assert response.json()["state"] == "NEW"
    assert response.json()["closed_at"] is None
    assert len(response.json()["fingerprint"]) == 64
    assert response.json()["first_seen_at"] == response.json()["last_seen_at"]


@pytest.mark.django_db
def test_deduplicate_open_event_and_create_after_close(api_client, service):
    payload = {"origin": "api", "value": 1}
    first = api_client.post(
        "/api/v1/events",
        {
            "origin": "SYSTEM",
            "title": "Evento repetido",
            "message": "Misma huella",
            "service_code": service.code,
            "payload": payload,
        },
        format="json",
    )
    assert first.status_code == 201
    event_id = first.json()["id"]

    second = api_client.post(
        "/api/v1/events",
        {
            "origin": "SYSTEM",
            "title": "Evento repetido",
            "message": "Misma huella",
            "service_code": service.code,
            "payload": payload,
        },
        format="json",
    )
    assert second.status_code == 200
    assert second.json()["occurrence_count"] == 2

    Event.objects.filter(id=event_id).update(state=EventState.CLOSED)
    third = api_client.post(
        "/api/v1/events",
        {
            "origin": "SYSTEM",
            "title": "Evento repetido",
            "message": "Misma huella",
            "service_code": service.code,
            "payload": payload,
        },
        format="json",
    )
    assert third.status_code == 201
    assert third.json()["id"] != event_id


@pytest.mark.django_db
def test_ingestion_key_is_idempotent_and_hidden(api_client):
    request = {
        "origin": "USER",
        "title": "Evento idempotente",
        "message": "Una sola ocurrencia",
        "ingestion_key": "clave-123",
        "payload": {"campo": "valor"},
    }
    first = api_client.post("/api/v1/events", request, format="json")
    second = api_client.post("/api/v1/events", request, format="json")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["occurrence_count"] == 1
    assert "_ingestion_key" not in second.json()["payload"]


@pytest.mark.django_db
def test_blank_ingestion_key_is_rejected(api_client):
    response = api_client.post(
        "/api/v1/events",
        {
            "origin": "USER",
            "title": "Evento con clave vacía",
            "message": "La clave de ingesta no puede estar vacía",
            "ingestion_key": "",
        },
        format="json",
    )

    assert response.status_code == 422
    assert "ingestion_key" in response.json()["fields"]


@pytest.mark.django_db
def test_validation_error_returns_422(api_client):
    response = api_client.post(
        "/api/v1/events",
        {"title": "", "payload": {"nested": "ok"}, "impact": "INVALID"},
        format="json",
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["detail"] == "Datos inválidos en la solicitud."
    assert isinstance(body["fields"], dict)


@pytest.mark.django_db
def test_list_filters_pagination_and_detail(api_client, service):
    first = api_client.post(
        "/api/v1/events",
        {
            "origin": "USER",
            "title": "Error de correos",
            "message": "No se envían correos",
            "service_code": service.code,
        },
        format="json",
    )
    second = api_client.post(
        "/api/v1/events",
        {
            "origin": "SYSTEM",
            "title": "Alerta de disco",
            "message": "Espacio insuficiente",
        },
        format="json",
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listing = api_client.get(
        "/api/v1/events",
        {
            "limit": 1,
            "offset": 0,
            "state": "NEW",
            "origin": "USER",
            "open": "true",
            "search": "correos",
            "ordering": "-created_at",
        },
    )
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] == 1
    assert len(body["results"]) == 1
    assert body["results"][0]["destination"] is None

    event_id = first.json()["id"]
    detail = api_client.get(f"/api/v1/events/{event_id}")
    assert detail.status_code == 200
    assert detail.json()["service"]["code"] == service.code
    assert detail.json()["routing"] == []

    no_service_id = second.json()["id"]
    no_service = api_client.get(f"/api/v1/events/{no_service_id}")
    assert no_service.status_code == 200
    assert "service" not in no_service.json()
    assert no_service.json()["routing"] == []


@pytest.mark.django_db
def test_detail_not_found_and_priority_matrix(api_client, service):
    PriorityMatrix.objects.create(impact="HIGH", urgency="HIGH", priority="P1")
    created = api_client.post(
        "/api/v1/events",
        {
            "origin": "SYSTEM",
            "title": "Prioridad crítica",
            "message": "Falla crítica",
            "service_code": service.code,
            "impact": "HIGH",
            "urgency": "HIGH",
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["priority"] == "P1"

    missing = api_client.get("/api/v1/events/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"
    assert missing.json()["detail"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"HTTP_AUTHORIZATION": "Bearer token-validado-en-gateway"},
        {"HTTP_X_API_KEY": "api-key-validada-en-gateway"},
        {
            "HTTP_AUTHORIZATION": "Bearer token-validado-en-gateway",
            "HTTP_X_API_KEY": "api-key-validada-en-gateway",
        },
    ],
)
def test_internal_service_accepts_optional_gateway_credentials(api_client, headers):
    response = api_client.get("/api/v1/events", **headers)

    assert response.status_code == 200
