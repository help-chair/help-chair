import pytest

from peticiones.models import CatalogItem, ServiceRequest

API_BASE = "/api/requests/v1"


@pytest.fixture
def catalog_item(db):
    return CatalogItem.objects.create(name="Alta de correo")


@pytest.fixture
def service_request(catalog_item):
    return ServiceRequest.objects.create(
        service=catalog_item,
        title="Necesito un correo nuevo",
        requester_id=1,
    )


def test_initial_status_is_new(service_request):
    assert service_request.status == ServiceRequest.Status.NEW
    assert service_request.approval_status == ServiceRequest.ApprovalStatus.NOT_REQUIRED


def test_valid_transition(service_request):
    assert service_request.can_transition_to(ServiceRequest.Status.ASSIGNED)


def test_invalid_transition(service_request):
    assert not service_request.can_transition_to(ServiceRequest.Status.CLOSED)


def test_closed_is_final(service_request):
    service_request.status = ServiceRequest.Status.CLOSED
    assert not service_request.can_transition_to(ServiceRequest.Status.REOPENED)


def _post(client, service_request, action_name, payload):
    return client.post(
        f"{API_BASE}/peticiones/{service_request.id}/{action_name}/",
        payload,
        content_type="application/json",
    )


def test_change_status_valid(client, service_request):
    response = _post(client, service_request, "cambiar-estado", {"estado": "asignado"})
    assert response.status_code == 200
    assert response.json()["estado"] == "asignado"


def test_change_status_invalid(client, service_request):
    response = _post(client, service_request, "cambiar-estado", {"estado": "cerrado"})
    assert response.status_code == 400


def test_cancel_requires_reason(client, service_request):
    response = _post(client, service_request, "cambiar-estado", {"estado": "cancelado"})
    assert response.status_code == 400


def test_cancel_with_reason(client, service_request):
    payload = {"estado": "cancelado", "motivo_cancelacion": "Ya no se necesita"}
    response = _post(client, service_request, "cambiar-estado", payload)
    assert response.status_code == 200
    assert response.json()["motivo_cancelacion"] == "Ya no se necesita"


def test_close_sets_closed_at(client, service_request):
    service_request.status = ServiceRequest.Status.RESOLVED
    service_request.save()
    response = _post(client, service_request, "cambiar-estado", {"estado": "cerrado"})
    assert response.status_code == 200
    assert response.json()["cerrada_en"] is not None


def test_assign_moves_to_assigned(client, service_request):
    response = _post(client, service_request, "asignar", {"asignado_a_id": 5})
    assert response.status_code == 200
    assert response.json()["asignado_a_id"] == 5
    assert response.json()["estado"] == "asignado"


def test_cannot_assign_when_closed(client, service_request):
    service_request.status = ServiceRequest.Status.CLOSED
    service_request.save()
    response = _post(client, service_request, "asignar", {"asignado_a_id": 5})
    assert response.status_code == 400


def test_change_enablement_approval_flow(client, catalog_item):
    create_res = client.post(
        f"{API_BASE}/peticiones/",
        {
            "tipo": "cambio",
            "servicio": catalog_item.id,
            "titulo": "Actualizar certificado TLS",
            "solicitante_id": 3,
            "aprobador_id": 10,
        },
        content_type="application/json",
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["tipo"] == "cambio"
    assert created["estado_aprobacion"] == "pendiente"

    request_obj = ServiceRequest.objects.get(id=created["id"])

    # Asignar antes de aprobar funciona, pero pasar a en_proceso se bloquea
    assert _post(client, request_obj, "asignar", {"asignado_a_id": 7}).status_code == 200
    blocked_res = _post(
        client, request_obj, "cambiar-estado", {"estado": "en_proceso"}
    )
    assert blocked_res.status_code == 400

    # Un aprobador distinto al designado es rechazado
    wrong_approver = _post(client, request_obj, "aprobar", {"aprobador_id": 99})
    assert wrong_approver.status_code == 400

    # El aprobador designado aprueba el cambio
    approved_res = _post(client, request_obj, "aprobar", {"aprobador_id": 10})
    assert approved_res.status_code == 200
    assert approved_res.json()["estado_aprobacion"] == "aprobado"
    assert approved_res.json()["aprobada_en"] is not None

    # Ahora sí puede pasar a en_proceso -> resuelto -> cerrado
    assert (
        _post(client, request_obj, "cambiar-estado", {"estado": "en_proceso"}).status_code
        == 200
    )


def test_change_enablement_rejection_cancels_request(client, catalog_item):
    create_res = client.post(
        f"{API_BASE}/peticiones/",
        {
            "tipo": "cambio",
            "servicio": catalog_item.id,
            "titulo": "Cambio en firewall de producción",
            "solicitante_id": 4,
            "aprobador_id": 10,
        },
        content_type="application/json",
    )
    request_obj = ServiceRequest.objects.get(id=create_res.json()["id"])

    reject_res = _post(
        client,
        request_obj,
        "rechazar",
        {"aprobador_id": 10, "motivo_rechazo": "Falta ventana de mantenimiento"},
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["estado_aprobacion"] == "rechazado"
    assert data["estado"] == "cancelado"
    assert data["motivo_rechazo"] == "Falta ventana de mantenimiento"


def test_filter_requests(client, catalog_item, service_request):
    ServiceRequest.objects.create(
        service=catalog_item,
        title="Acceso VPN",
        requester_id=2,
        assignee_id=9,
        status=ServiceRequest.Status.ASSIGNED,
    )

    by_status = client.get(f"{API_BASE}/peticiones/?estado=asignado")
    assert by_status.status_code == 200
    assert len(by_status.json()) == 1
    assert by_status.json()[0]["titulo"] == "Acceso VPN"

    by_assignee = client.get(f"{API_BASE}/peticiones/?asignado_a_id=9")
    assert by_assignee.status_code == 200
    assert len(by_assignee.json()) == 1

    by_requester = client.get(f"{API_BASE}/peticiones/?solicitante_id=1")
    assert by_requester.status_code == 200
    assert len(by_requester.json()) == 1
    assert by_requester.json()[0]["id"] == str(service_request.id)


def test_filter_requests_invalid_id(client):
    response = client.get(f"{API_BASE}/peticiones/?asignado_a_id=no-es-numero")
    assert response.status_code == 400


def test_create_and_edit_catalog_item(db, client):
    create_res = client.post(
        f"{API_BASE}/servicios/",
        {"nombre": "Acceso a VPN", "descripcion": "Alta en red remota"},
        content_type="application/json",
    )
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]

    patch_res = client.patch(
        f"{API_BASE}/servicios/{item_id}/",
        {"descripcion": "Alta en VPN corporativa", "activo": False},
        content_type="application/json",
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["activo"] is False

    active_list = client.get(f"{API_BASE}/servicios/")
    assert active_list.status_code == 200
    assert all(item["id"] != item_id for item in active_list.json())

    all_list = client.get(f"{API_BASE}/servicios/?incluir_inactivos=true")
    assert any(item["id"] == item_id for item in all_list.json())
    assert client.get(f"{API_BASE}/servicios/{item_id}/").status_code == 200


def test_cannot_create_request_with_inactive_service(client, catalog_item):
    catalog_item.is_active = False
    catalog_item.save()

    response = client.post(
        f"{API_BASE}/peticiones/",
        {
            "servicio": catalog_item.id,
            "titulo": "Intento en servicio inactivo",
            "solicitante_id": 1,
        },
        content_type="application/json",
    )
    assert response.status_code == 400