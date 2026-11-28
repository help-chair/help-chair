import pytest
from django.core.management import call_command
from django.test import override_settings
from rest_framework_simplejwt.tokens import AccessToken

from peticiones.consumers import process_routed_event
from peticiones.models import CatalogItem, ServiceRequest

API_BASE = "/api/requests/v1"


def _build_access_jwt(
    user_id: int = 10, role: str = "agente", empresa: str = "empresa-demo"
) -> str:
    token = AccessToken()
    token["sub"] = str(user_id)
    token["iss"] = "help-chair-access"
    token["rol"] = role
    token["empresa"] = empresa
    return str(token)


@pytest.mark.django_db
def test_e2e_event_to_closed_and_reopened_lifecycle(client):
    """Flujo E2E Fase 3: evento NATS -> ciclo completo -> cerrado y reabierto."""
    CatalogItem.objects.create(name="Acceso VPN", is_active=True)

    envelope = {
        "id": "env-fase3-001",
        "type": "event.routed",
        "source": "events",
        "payload": {
            "event_id": "evt-fase3-001",
            "destination": "REQUESTS",
            "category": "REQUEST",
            "service_code": "Acceso VPN",
            "title": "Alta de VPN desde evento automático",
            "message": "Usuario nuevo requiere acceso remoto",
            "reporter_ref": "42",
        },
    }

    created_request, created = process_routed_event(envelope)
    assert created is True
    assert created_request is not None
    assert created_request.status == ServiceRequest.Status.NEW

    req_id = created_request.id

    # 1. nuevo -> asignado
    res_assign = client.post(
        f"{API_BASE}/peticiones/{req_id}/asignar/",
        {"asignado_a_id": "7"},
        content_type="application/json",
    )
    assert res_assign.status_code == 200
    assert res_assign.json()["estado"] == "asignado"

    # 2. asignado -> en_proceso
    res_progress = client.post(
        f"{API_BASE}/peticiones/{req_id}/cambiar-estado/",
        {"estado": "en_proceso"},
        content_type="application/json",
    )
    assert res_progress.status_code == 200
    assert res_progress.json()["estado"] == "en_proceso"

    # 3. en_proceso -> resuelto
    res_resolved = client.post(
        f"{API_BASE}/peticiones/{req_id}/cambiar-estado/",
        {"estado": "resuelto"},
        content_type="application/json",
    )
    assert res_resolved.status_code == 200
    assert res_resolved.json()["estado"] == "resuelto"

    # 4. resuelto -> cerrado
    res_closed = client.post(
        f"{API_BASE}/peticiones/{req_id}/cambiar-estado/",
        {"estado": "cerrado"},
        content_type="application/json",
    )
    assert res_closed.status_code == 200
    assert res_closed.json()["estado"] == "cerrado"
    assert res_closed.json()["cerrada_en"] is not None

    # 5. Reapertura: resuelto -> reabierto -> asignado
    second_req = ServiceRequest.objects.create(
        service=created_request.service,
        title="Petición con reapertura",
        requester_id="42",
        status=ServiceRequest.Status.RESOLVED,
    )
    res_reopen = client.post(
        f"{API_BASE}/peticiones/{second_req.id}/cambiar-estado/",
        {"estado": "reabierto"},
        content_type="application/json",
    )
    assert res_reopen.status_code == 200
    assert res_reopen.json()["estado"] == "reabierto"

    res_reassign = client.post(
        f"{API_BASE}/peticiones/{second_req.id}/asignar/",
        {"asignado_a_id": "8"},
        content_type="application/json",
    )
    assert res_reassign.status_code == 200
    assert res_reassign.json()["estado"] == "asignado"


@pytest.mark.django_db
@override_settings(JWT_AUTH_ENABLED=True)
def test_jwt_authentication_from_access_service(client):
    """Valida tokens JWT emitidos por Accesos y restringe edición de catálogo por rol."""
    # Sin token -> 401
    unauth_res = client.get(f"{API_BASE}/peticiones/")
    assert unauth_res.status_code == 401

    # Usuario solicitante puede listar y crear peticiones, pero no editar catálogo (403)
    solicitante_token = _build_access_jwt(user_id=15, role="usuario")
    auth_user = {"HTTP_AUTHORIZATION": f"Bearer {solicitante_token}"}

    list_res = client.get(f"{API_BASE}/peticiones/", **auth_user)
    assert list_res.status_code == 200

    forbidden_catalog = client.post(
        f"{API_BASE}/servicios/",
        {"nombre": "Servicio no autorizado"},
        content_type="application/json",
        **auth_user,
    )
    assert forbidden_catalog.status_code == 403

    # Agente/admin sí puede crear servicios en el catálogo (201)
    agent_token = _build_access_jwt(user_id=20, role="agente")
    auth_agent = {"HTTP_AUTHORIZATION": f"Bearer {agent_token}"}

    allowed_catalog = client.post(
        f"{API_BASE}/servicios/",
        {"nombre": "Alta de equipo"},
        content_type="application/json",
        **auth_agent,
    )
    assert allowed_catalog.status_code == 201


@pytest.mark.django_db
def test_seed_command_is_idempotent():
    call_command("seed")
    first_catalog_count = CatalogItem.objects.count()
    first_req_count = ServiceRequest.objects.count()

    call_command("seed")
    assert CatalogItem.objects.count() == first_catalog_count
    assert ServiceRequest.objects.count() == first_req_count
    assert first_catalog_count >= 3
    assert first_req_count >= 3
