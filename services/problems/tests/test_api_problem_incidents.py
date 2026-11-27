"""Incidentes vinculados a un problema, por su ID de texto en Incidencias (#272)."""

from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from django.utils import timezone

from problems.models import ProblemIncident
from tests.factories import ProblemFactory, ProblemIncidentFactory

pytestmark = pytest.mark.django_db


def incidents_url(problem_pk):
    return f"/api/problems/v1/problemas/{problem_pk}/incidentes/"


def link_url(problem_pk, incident_id):
    return f"{incidents_url(problem_pk)}{incident_id}/"


@pytest.fixture(scope="module")
def contract():
    path = Path(__file__).resolve().parents[3] / "contracts/problems/openapi.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["components"]["schemas"]


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert body["codigo"] == code
    assert isinstance(body["detalle"], str) and body["detalle"]
    assert set(body) <= {"codigo", "detalle", "campos"}
    return body


# --- List ----------------------------------------------------------------------------------------


def test_list_without_links_is_an_empty_array(api):
    problem = ProblemFactory()
    response = api.get(incidents_url(problem.pk))
    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_only_this_problems_links_oldest_first(api, contract):
    problem = ProblemFactory()
    newer = ProblemIncidentFactory(problem=problem, incident_id="INC-2")
    older = ProblemIncidentFactory(problem=problem, incident_id="INC-1")
    ProblemIncidentFactory(incident_id="INC-3")
    ProblemIncident.objects.filter(pk=older.pk).update(
        linked_at=timezone.now() - timedelta(hours=1)
    )
    body = api.get(incidents_url(problem.pk)).json()
    assert [item["incidente_id"] for item in body] == ["INC-1", "INC-2"]
    assert [item["id"] for item in body] == [older.pk, newer.pk]
    assert all(item["problema_id"] == problem.pk for item in body)
    assert set(body[0]) == set(contract["ProblemaIncidente"]["properties"])
    assert set(body[0]) == set(contract["ProblemaIncidente"]["required"])


def test_list_is_not_paginated(api):
    problem = ProblemFactory()
    ProblemIncidentFactory.create_batch(25, problem=problem)
    response = api.get(incidents_url(problem.pk), {"page": "abc", "page_size": 5})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 25


@pytest.mark.parametrize("pk", ["999999", "abc"])
def test_list_for_missing_problem_is_404(api, pk):
    assert_error(api.get(incidents_url(pk)), 404, "no_encontrado")


# --- Link ----------------------------------------------------------------------------------------


def test_link_incident_returns_201_with_the_link(api, contract):
    problem = ProblemFactory()
    response = api.post(incidents_url(problem.pk), {"incidente_id": "INC-1"}, format="json")
    assert response.status_code == 201
    body = response.json()
    assert set(body) == set(contract["ProblemaIncidente"]["properties"])
    assert body["problema_id"] == problem.pk
    assert body["incidente_id"] == "INC-1"
    assert body["vinculado_en"]
    link = ProblemIncident.objects.get(pk=body["id"])
    assert (link.problem_id, link.incident_id) == (problem.pk, "INC-1")


def test_read_only_fields_in_the_body_are_ignored(api):
    problem, other = ProblemFactory.create_batch(2)
    payload = {
        "incidente_id": "INC-1",
        "id": 777,
        "problema_id": other.pk,
        "vinculado_en": "2000-01-01T00:00:00Z",
    }
    body = api.post(incidents_url(problem.pk), payload, format="json").json()
    assert body["problema_id"] == problem.pk
    assert body["id"] != 777
    assert not body["vinculado_en"].startswith("2000")
    assert not other.incidents.exists()


@pytest.mark.parametrize("incident_id", ["cualquier-texto 123", "x" * 64, "123"])
def test_incident_id_is_stored_as_text_without_checking_incidencias(api, incident_id):
    problem = ProblemFactory()
    response = api.post(incidents_url(problem.pk), {"incidente_id": incident_id}, format="json")
    assert response.status_code == 201
    assert response.json()["incidente_id"] == incident_id


def test_same_incident_can_be_linked_to_two_different_problems(api):
    first, second = ProblemFactory.create_batch(2)
    for problem in (first, second):
        response = api.post(incidents_url(problem.pk), {"incidente_id": "INC-1"}, format="json")
        assert response.status_code == 201
    assert ProblemIncident.objects.filter(incident_id="INC-1").count() == 2


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"incidente_id": ""},
        {"incidente_id": "   "},
        {"incidente_id": "x" * 65},
        {"incidente_id": None},
    ],
)
def test_link_with_invalid_incident_id_is_400(api, payload):
    problem = ProblemFactory()
    response = api.post(incidents_url(problem.pk), payload, format="json")
    body = assert_error(response, 400, "datos_invalidos")
    assert set(body["campos"]) == {"incidente_id"}
    assert isinstance(body["campos"]["incidente_id"], str)
    assert not ProblemIncident.objects.exists()


def test_link_with_malformed_json_is_400(api):
    problem = ProblemFactory()
    response = api.generic(
        "POST", incidents_url(problem.pk), "{no es json", content_type="application/json"
    )
    assert_error(response, 400, "datos_invalidos")


def test_link_to_missing_problem_is_404(api):
    response = api.post(incidents_url(999999), {"incidente_id": "INC-1"}, format="json")
    assert_error(response, 404, "no_encontrado")
    assert not ProblemIncident.objects.exists()


def test_link_already_linked_incident_is_409(api):
    link = ProblemIncidentFactory(incident_id="INC-1")
    response = api.post(incidents_url(link.problem_id), {"incidente_id": "INC-1"}, format="json")
    assert response.status_code == 409
    assert response.json() == {
        "codigo": "incidente_ya_vinculado",
        "detalle": f"INC-1 ya está vinculado a PRB-{link.problem_id}.",
    }
    assert ProblemIncident.objects.count() == 1


def test_link_still_works_after_a_409(api):
    link = ProblemIncidentFactory(incident_id="INC-1")
    url = incidents_url(link.problem_id)
    assert api.post(url, {"incidente_id": "INC-1"}, format="json").status_code == 409
    assert api.post(url, {"incidente_id": "INC-2"}, format="json").status_code == 201
    assert link.problem.incidents.count() == 2


# --- Unlink --------------------------------------------------------------------------------------


def test_unlink_returns_204_and_keeps_other_links(api):
    problem = ProblemFactory()
    ProblemIncidentFactory(problem=problem, incident_id="INC-1")
    kept = ProblemIncidentFactory(problem=problem, incident_id="INC-2")
    elsewhere = ProblemIncidentFactory(incident_id="INC-1")
    response = api.delete(link_url(problem.pk, "INC-1"))
    assert response.status_code == 204
    assert response.content == b""
    assert list(problem.incidents.all()) == [kept]
    assert ProblemIncident.objects.filter(pk=elsewhere.pk).exists()


def test_unlink_incident_id_with_spaces_encoded_in_the_url(api):
    link = ProblemIncidentFactory(incident_id="INC 1")
    assert api.delete(link_url(link.problem_id, "INC%201")).status_code == 204
    assert not ProblemIncident.objects.exists()


def test_incident_can_be_linked_again_after_unlinking(api):
    link = ProblemIncidentFactory(incident_id="INC-1")
    api.delete(link_url(link.problem_id, "INC-1"))
    response = api.post(incidents_url(link.problem_id), {"incidente_id": "INC-1"}, format="json")
    assert response.status_code == 201


def test_unlink_incident_not_linked_is_404(api):
    problem = ProblemFactory()
    body = assert_error(api.delete(link_url(problem.pk, "INC-9")), 404, "no_encontrado")
    assert body["detalle"] == f"INC-9 no está vinculado a PRB-{problem.pk}."


def test_unlink_incident_linked_only_to_another_problem_is_404(api):
    problem = ProblemFactory()
    other_link = ProblemIncidentFactory(incident_id="INC-1")
    assert_error(api.delete(link_url(problem.pk, "INC-1")), 404, "no_encontrado")
    assert ProblemIncident.objects.filter(pk=other_link.pk).exists()


def test_unlink_with_an_id_longer_than_64_is_a_json_404(api):
    problem = ProblemFactory()
    assert_error(api.delete(link_url(problem.pk, "x" * 65)), 404, "no_encontrado")


@pytest.mark.parametrize("pk", ["999999", "abc"])
def test_unlink_for_missing_problem_is_404(api, pk):
    body = assert_error(api.delete(link_url(pk, "INC-1")), 404, "no_encontrado")
    assert body["detalle"] == "No existe el recurso solicitado."


# --- Methods not allowed -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "route"),
    [
        ("put", "collection"),
        ("patch", "collection"),
        ("delete", "collection"),
        ("get", "item"),
        ("post", "item"),
        ("put", "item"),
        ("patch", "item"),
    ],
)
def test_methods_not_allowed_are_405(api, method, route):
    link = ProblemIncidentFactory(incident_id="INC-1")
    urls = {
        "collection": incidents_url(link.problem_id),
        "item": link_url(link.problem_id, "INC-1"),
    }
    response = getattr(api, method)(urls[route], {"incidente_id": "INC-2"}, format="json")
    body = assert_error(response, 405, "metodo_no_permitido")
    assert method.upper() in body["detalle"]
    assert list(ProblemIncident.objects.values_list("incident_id", flat=True)) == ["INC-1"]
