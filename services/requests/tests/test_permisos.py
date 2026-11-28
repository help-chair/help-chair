"""Permisos con el JWT de Accesos: claims `sub` (UUID), `rol` y `permisos`."""

import pytest
from django.test import override_settings

from peticiones.models import CatalogItem, ServiceRequest
from tests.test_integracion_fase3 import _build_access_jwt

API_BASE = "/api/requests/v1"
ANA = "3f2a9c4e-8d1b-4b5a-9e2f-1c7d6a5b4e3f"
LUIS = "9b1d2c3e-4f5a-4b6c-8d7e-0f1a2b3c4d5e"
AGENT = "5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9"
ADMIN = "0a1b2c3d-4e5f-4a6b-8c7d-e8f9a0b1c2d3"

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("jwt_on")]


@pytest.fixture
def jwt_on():
    with override_settings(JWT_AUTH_ENABLED=True):
        yield


def auth(user_id: str, role: str) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {_build_access_jwt(user_id=user_id, role=role)}"}


def post(client, url: str, data: dict, headers: dict):
    return client.post(f"{API_BASE}{url}", data, content_type="application/json", **headers)


@pytest.fixture
def catalog_item():
    return CatalogItem.objects.create(name="Correo corporativo")


@pytest.fixture
def ana_request(catalog_item):
    return ServiceRequest.objects.create(
        service=catalog_item, title="Buzón de Ana", requester_id=ANA
    )


@pytest.fixture
def luis_request(catalog_item):
    return ServiceRequest.objects.create(
        service=catalog_item, title="Buzón de Luis", requester_id=LUIS
    )


def test_token_without_permissions_is_rejected(client):
    """Un token sin el claim `permisos` no pasa (antes se permitía todo sin rol)."""
    response = client.get(f"{API_BASE}/peticiones/", **auth(ANA, "rol-desconocido"))
    assert response.status_code == 403


def test_end_user_only_sees_own_requests(client, ana_request, luis_request):
    headers = auth(ANA, "usuario_final")

    listed = client.get(f"{API_BASE}/peticiones/", **headers).json()
    assert [item["id"] for item in listed] == [str(ana_request.id)]

    other = client.get(f"{API_BASE}/peticiones/{luis_request.id}/", **headers)
    assert other.status_code == 404


def test_agent_sees_every_request(client, ana_request, luis_request):
    listed = client.get(f"{API_BASE}/peticiones/", **auth(AGENT, "agente_n1")).json()
    assert len(listed) == 2


def test_end_user_always_creates_in_own_name(client, catalog_item):
    response = post(
        client,
        "/peticiones/",
        {"servicio": catalog_item.id, "titulo": "Monitor", "solicitante_id": LUIS},
        auth(ANA, "usuario_final"),
    )
    assert response.status_code == 201
    assert response.json()["solicitante_id"] == ANA


def test_end_user_can_cancel_but_not_work_on_own_request(client, ana_request):
    headers = auth(ANA, "usuario_final")
    url = f"/peticiones/{ana_request.id}/cambiar-estado/"

    assert post(client, url, {"estado": "asignado"}, headers).status_code == 403

    cancelled = post(
        client, url, {"estado": "cancelado", "motivo_cancelacion": "Ya no la necesito"}, headers
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["motivo_cancelacion"] == "Ya no la necesito"


def test_end_user_cannot_change_someone_elses_request(client, luis_request):
    response = post(
        client,
        f"/peticiones/{luis_request.id}/cambiar-estado/",
        {"estado": "cancelado", "motivo_cancelacion": "x"},
        auth(ANA, "usuario_final"),
    )
    assert response.status_code == 404


def test_only_support_assigns(client, ana_request):
    url = f"/peticiones/{ana_request.id}/asignar/"
    assert (
        post(client, url, {"asignado_a_id": AGENT}, auth(ANA, "usuario_final")).status_code == 403
    )

    assigned = post(client, url, {"asignado_a_id": AGENT}, auth(AGENT, "agente_n1"))
    assert assigned.status_code == 200
    assert assigned.json()["asignado_a_id"] == AGENT


def test_only_admin_approves_and_only_as_themselves(client, catalog_item):
    change = ServiceRequest.objects.create(
        service=catalog_item,
        title="Abrir puerto 443",
        requester_id=ANA,
        request_type=ServiceRequest.RequestType.CHANGE,
        approval_status=ServiceRequest.ApprovalStatus.PENDING,
    )
    url = f"/peticiones/{change.id}/aprobar/"

    as_agent = post(client, url, {"aprobador_id": AGENT}, auth(AGENT, "agente_n2"))
    assert as_agent.status_code == 403

    spoofed = post(client, url, {"aprobador_id": LUIS}, auth(ADMIN, "administrador"))
    assert spoofed.status_code == 403

    approved = post(client, url, {"aprobador_id": ADMIN}, auth(ADMIN, "administrador"))
    assert approved.status_code == 200
    assert approved.json()["estado_aprobacion"] == "aprobado"
    assert approved.json()["aprobador_id"] == ADMIN


def test_only_the_requester_answers_the_survey(client, catalog_item):
    resolved = ServiceRequest.objects.create(
        service=catalog_item,
        title="Licencia",
        requester_id=ANA,
        status=ServiceRequest.Status.RESOLVED,
    )
    url = f"/peticiones/{resolved.id}/encuesta/"

    as_agent = post(client, url, {"calificacion": 5}, auth(AGENT, "agente_n1"))
    assert as_agent.status_code == 403
    as_luis = post(client, url, {"calificacion": 1}, auth(LUIS, "usuario_final"))
    assert as_luis.status_code == 404

    answered = post(client, url, {"calificacion": 5}, auth(ANA, "usuario_final"))
    assert answered.status_code == 201
    assert resolved.survey.respondent_id == ANA
