"""API CRUD de problemas: listado, alta, consulta y actualización parcial (#271)."""

from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from django.utils import timezone

from problems.models import Problem
from tests.factories import ProblemFactory

pytestmark = pytest.mark.django_db

LIST_URL = "/api/problems/v1/problemas/"


def detail_url(pk):
    return f"{LIST_URL}{pk}/"


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


def test_empty_list_returns_the_paginated_envelope(api):
    response = api.get(LIST_URL)
    assert response.status_code == 200
    assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}


def test_list_is_ordered_newest_first(api):
    oldest, newest, middle = ProblemFactory.create_batch(3)
    now = timezone.now()
    for problem, hours in ((oldest, 3), (middle, 2), (newest, 1)):
        Problem.objects.filter(pk=problem.pk).update(created_at=now - timedelta(hours=hours))
    ids = [p["id"] for p in api.get(LIST_URL).json()["results"]]
    assert ids == [newest.pk, middle.pk, oldest.pk]


def test_each_item_has_the_problema_schema_fields(api, contract):
    ProblemFactory()
    item = api.get(LIST_URL).json()["results"][0]
    assert set(item) == set(contract["Problema"]["properties"])
    assert set(item) == set(contract["Problema"]["required"])


def test_default_page_size_is_20(api):
    ProblemFactory.create_batch(25)
    first = api.get(LIST_URL).json()
    assert first["count"] == 25
    assert len(first["results"]) == 20
    assert first["previous"] is None
    assert "page=2" in first["next"]
    second = api.get(LIST_URL, {"page": 2}).json()
    assert len(second["results"]) == 5
    assert second["next"] is None
    assert second["previous"] is not None


def test_page_size_changes_the_page_length(api):
    ProblemFactory.create_batch(7)
    body = api.get(LIST_URL, {"page_size": 5}).json()
    assert len(body["results"]) == 5
    assert "page_size=5" in body["next"]


def test_page_size_is_capped_at_100(api):
    ProblemFactory.create_batch(101)
    body = api.get(LIST_URL, {"page_size": 500}).json()
    assert body["count"] == 101
    assert len(body["results"]) == 100


def test_out_of_range_page_is_404(api):
    ProblemFactory.create_batch(3)
    body = assert_error(api.get(LIST_URL, {"page": 2}), 404, "no_encontrado")
    assert "campos" not in body


@pytest.mark.parametrize(
    ("param", "value"),
    [("page", "0"), ("page", "abc"), ("page", "-1"), ("page_size", "0"), ("page_size", "x")],
)
def test_invalid_pagination_params_are_400(api, param, value):
    body = assert_error(api.get(LIST_URL, {param: value}), 400, "datos_invalidos")
    assert set(body["campos"]) == {param}


@pytest.mark.parametrize(
    ("param", "field", "value", "other"),
    [
        ("estado", "status", Problem.Status.IN_ANALYSIS, Problem.Status.REGISTERED),
        ("prioridad", "priority", Problem.Priority.CRITICAL, Problem.Priority.LOW),
        ("origen", "origin", Problem.Origin.PATTERN, Problem.Origin.MANUAL),
    ],
)
def test_valid_filters(api, param, field, value, other):
    expected = ProblemFactory(**{field: value})
    ProblemFactory(**{field: other})
    body = api.get(LIST_URL, {param: value}).json()
    assert body["count"] == 1
    assert body["results"][0]["id"] == expected.pk


def test_filters_can_be_combined(api):
    expected = ProblemFactory(priority="alta", origin="patron")
    ProblemFactory(priority="alta", origin="manual")
    ProblemFactory(priority="baja", origin="patron")
    body = api.get(LIST_URL, {"prioridad": "alta", "origen": "patron"}).json()
    assert [p["id"] for p in body["results"]] == [expected.pk]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("estado", "abierto"),
        ("estado", ""),
        ("prioridad", "urgente"),
        ("prioridad", "ALTA"),
        ("origen", "automatico"),
    ],
)
def test_invalid_filters_are_400(api, field, value):
    body = assert_error(api.get(LIST_URL, {field: value}), 400, "datos_invalidos")
    assert body["campos"] == {field: f'"{value}" no es una opción válida.'}


def test_several_invalid_filters_are_reported_together(api):
    body = assert_error(api.get(LIST_URL, {"estado": "x", "origen": "y"}), 400, "datos_invalidos")
    assert set(body["campos"]) == {"estado", "origen"}


# --- Create --------------------------------------------------------------------------------------


def test_create_with_required_fields_applies_defaults(api, contract):
    payload = {"titulo": "Correo caído", "descripcion": "No envía."}
    response = api.post(LIST_URL, payload, format="json")
    assert response.status_code == 201
    body = response.json()
    assert set(body) == set(contract["Problema"]["properties"])
    assert body["estado"] == "registrado"
    assert body["prioridad"] == "media"
    assert body["origen"] == "manual"
    assert body["causa_raiz"] == ""
    assert body["asignado_a_id"] == ""
    assert body["resuelto_en"] is None
    assert Problem.objects.get(pk=body["id"]).title == "Correo caído"


def test_create_with_all_fields(api):
    payload = {
        "titulo": "Caída del correo cada lunes",
        "descripcion": "El servidor deja de responder.",
        "prioridad": "alta",
        "origen": "patron",
        "causa_raiz": "Certificado vencido.",
        "asignado_a_id": "usr-17",
    }
    body = api.post(LIST_URL, payload, format="json").json()
    assert {field: body[field] for field in payload} == payload
    assert body["estado"] == "registrado"


def test_create_is_always_registered_even_if_another_status_is_sent(api):
    payload = {"titulo": "T", "descripcion": "D", "estado": "cerrado", "resuelto_en": None}
    response = api.post(LIST_URL, payload, format="json")
    assert response.status_code == 201
    assert response.json()["estado"] == "registrado"
    assert Problem.objects.get().status == "registrado"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"descripcion": "D"}, "titulo"),
        ({"titulo": "T"}, "descripcion"),
        ({"titulo": "", "descripcion": "D"}, "titulo"),
        ({"titulo": "x" * 201, "descripcion": "D"}, "titulo"),
        ({"titulo": "T", "descripcion": "D", "prioridad": "urgente"}, "prioridad"),
        ({"titulo": "T", "descripcion": "D", "origen": "otro"}, "origen"),
        ({"titulo": "T", "descripcion": "D", "asignado_a_id": "u" * 65}, "asignado_a_id"),
    ],
)
def test_create_with_invalid_data_is_400(api, payload, field):
    body = assert_error(api.post(LIST_URL, payload, format="json"), 400, "datos_invalidos")
    assert field in body["campos"]
    assert all(isinstance(message, str) for message in body["campos"].values())
    assert not Problem.objects.exists()


def test_validation_error_format(api):
    body = api.post(LIST_URL, {}, format="json").json()
    assert body == {
        "codigo": "datos_invalidos",
        "detalle": "La solicitud tiene campos inválidos.",
        "campos": {
            "titulo": "Este campo es requerido.",
            "descripcion": "Este campo es requerido.",
        },
    }


def test_malformed_json_is_400(api):
    response = api.generic("POST", LIST_URL, "{no es json", content_type="application/json")
    body = assert_error(response, 400, "datos_invalidos")
    assert "campos" not in body


# --- Retrieve ------------------------------------------------------------------------------------


def test_retrieve_a_problem(api):
    problem = ProblemFactory(status="resuelto", assignee_id="usr-1")
    response = api.get(detail_url(problem.pk))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == problem.pk
    assert body["estado"] == "resuelto"
    assert body["resuelto_en"] is not None


@pytest.mark.parametrize("pk", ["999999", "abc", "0", "99999999999999999999"])
def test_retrieve_missing_problem_is_404(api, pk):
    body = api.get(detail_url(pk)).json()
    assert body == {"codigo": "no_encontrado", "detalle": "No existe el recurso solicitado."}


# --- Partial update ------------------------------------------------------------------------------


def test_patch_updates_only_the_sent_fields(api):
    problem = ProblemFactory(status="en_analisis", priority="baja")
    payload = {"prioridad": "critica", "asignado_a_id": "usr-17", "causa_raiz": "Disco lleno."}
    response = api.patch(detail_url(problem.pk), payload, format="json")
    assert response.status_code == 200
    body = response.json()
    assert {field: body[field] for field in payload} == payload
    assert body["titulo"] == problem.title
    assert body["estado"] == "en_analisis"
    problem.refresh_from_db()
    assert problem.priority == "critica"


def test_patch_title_and_description(api):
    problem = ProblemFactory()
    payload = {"titulo": "Nuevo", "descripcion": "Otra"}
    body = api.patch(detail_url(problem.pk), payload, format="json").json()
    assert (body["titulo"], body["descripcion"]) == ("Nuevo", "Otra")


@pytest.mark.parametrize(
    ("field", "value"),
    [("estado", "cerrado"), ("origen", "patron")],
)
def test_patch_rejects_state_and_origin(api, field, value):
    problem = ProblemFactory()
    payload = {field: value, "prioridad": "alta"}
    response = api.patch(detail_url(problem.pk), payload, format="json")
    body = assert_error(response, 400, "datos_invalidos")
    assert set(body["campos"]) == {field}
    problem.refresh_from_db()
    assert (problem.status, problem.origin, problem.priority) == ("registrado", "manual", "media")


@pytest.mark.parametrize("field", ["id", "resuelto_en", "creado_en", "actualizado_en", "otro"])
def test_patch_rejects_fields_outside_the_schema(api, field):
    problem = ProblemFactory()
    response = api.patch(detail_url(problem.pk), {field: "x"}, format="json")
    body = assert_error(response, 400, "datos_invalidos")
    assert body["campos"] == {field: "Este campo no se puede modificar."}


@pytest.mark.parametrize("payload", [{}, None])
def test_patch_with_empty_body_is_400(api, payload):
    problem = ProblemFactory()
    response = api.patch(detail_url(problem.pk), payload, format="json")
    assert response.json() == {"codigo": "datos_invalidos", "detalle": "Envía al menos un campo."}
    assert response.status_code == 400


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"titulo": ""}, "titulo"),
        ({"descripcion": ""}, "descripcion"),
        ({"prioridad": "urgente"}, "prioridad"),
        ({"titulo": None}, "titulo"),
    ],
)
def test_patch_with_invalid_data_is_400(api, payload, field):
    problem = ProblemFactory()
    response = api.patch(detail_url(problem.pk), payload, format="json")
    body = assert_error(response, 400, "datos_invalidos")
    assert field in body["campos"]


def test_patch_missing_problem_is_404(api):
    response = api.patch(detail_url(999999), {"titulo": "X"}, format="json")
    assert_error(response, 404, "no_encontrado")


# --- Methods not allowed -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "route"),
    [
        ("put", "detail"),
        ("delete", "detail"),
        ("post", "detail"),
        ("put", "list"),
        ("patch", "list"),
        ("delete", "list"),
        ("get", "state"),
        ("patch", "state"),
    ],
)
def test_methods_not_allowed_are_405(api, method, route):
    problem = ProblemFactory()
    urls = {
        "list": LIST_URL,
        "detail": detail_url(problem.pk),
        "state": f"{detail_url(problem.pk)}estado/",
    }
    response = getattr(api, method)(urls[route], {"titulo": "X"}, format="json")
    body = assert_error(response, 405, "metodo_no_permitido")
    assert method.upper() in body["detalle"]
    assert Problem.objects.filter(pk=problem.pk).exists()
