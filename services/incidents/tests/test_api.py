"""API v0 /api/incidents/ (issue #122)."""

import pytest
from rest_framework.test import APIClient

from incidents.models import Incident, Status

pytestmark = pytest.mark.django_db
URL = "/api/incidents/"


@pytest.fixture
def api():
    return APIClient()


def nuevo(api, **extra):
    data = {"title": "Correo caído", "impact": "alto", "urgency": "alta", "reported_by": "u1"}
    return api.post(URL, {**data, **extra}, format="json")


def test_crear_calcula_prioridad_y_empieza_en_nuevo(api):
    response = nuevo(api)
    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "P1"
    assert body["status"] == "nuevo"
    assert body["code"].startswith("INC-")


def test_no_se_puede_crear_en_otro_estado(api):
    response = nuevo(api, status="cerrado")
    assert response.status_code == 400
    assert "status" in response.json()


def test_la_prioridad_no_se_puede_mandar_a_mano(api):
    response = nuevo(api, impact="bajo", urgency="baja", priority="P1")
    assert response.json()["priority"] == "P4"


def test_impacto_invalido_da_400(api):
    response = nuevo(api, impact="enorme")
    assert response.status_code == 400
    assert "impact" in response.json()


def test_listar_paginado_y_filtrar(api):
    nuevo(api)
    nuevo(api, title="Impresora", impact="bajo", urgency="baja")
    body = api.get(URL).json()
    assert body["count"] == 2
    assert body["results"][0]["priority"] == "P1"  # P1 primero
    filtrado = api.get(URL, {"priority": "P4"}).json()
    assert [i["title"] for i in filtrado["results"]] == ["Impresora"]


def test_ver_detalle(api):
    pk = nuevo(api).json()["id"]
    assert api.get(f"{URL}{pk}/").json()["id"] == pk


def test_asignar_requiere_agente(api):
    pk = nuevo(api).json()["id"]
    response = api.patch(f"{URL}{pk}/", {"status": "asignado"}, format="json")
    assert response.status_code == 400
    assert "assigned_to" in response.json()


def test_flujo_feliz_hasta_cerrado(api):
    pk = nuevo(api).json()["id"]
    url = f"{URL}{pk}/"
    response = api.patch(url, {"status": "asignado", "assigned_to": "agente-1"}, format="json")
    assert response.status_code == 200
    for status in ("en_proceso", "resuelto", "cerrado"):
        response = api.patch(url, {"status": status}, format="json")
        assert response.status_code == 200, response.json()
    incident = Incident.objects.get(pk=pk)
    assert incident.status == Status.CLOSED
    assert incident.resolved_at is not None
    assert incident.closed_at is not None


def test_transicion_invalida_da_400(api):
    pk = nuevo(api).json()["id"]
    response = api.patch(f"{URL}{pk}/", {"status": "cerrado"}, format="json")
    assert response.status_code == 400
    assert "status" in response.json()


def test_cambiar_urgencia_recalcula_prioridad(api):
    pk = nuevo(api).json()["id"]
    response = api.patch(f"{URL}{pk}/", {"urgency": "baja"}, format="json")
    assert response.json()["priority"] == "P3"


def test_no_se_permite_borrar_ni_put(api):
    pk = nuevo(api).json()["id"]
    assert api.delete(f"{URL}{pk}/").status_code == 405
    assert api.put(f"{URL}{pk}/", {}, format="json").status_code == 405
