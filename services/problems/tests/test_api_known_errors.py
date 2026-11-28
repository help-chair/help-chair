"""API de errores conocidos: listado, alta, consulta y actualización parcial (#273)."""

from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from django.utils import timezone

from problems.models import KnownError
from tests.factories import KnownErrorFactory, ProblemFactory

pytestmark = pytest.mark.django_db

LIST_URL = "/api/problems/v1/errores-conocidos/"


def detail_url(pk):
    return f"{LIST_URL}{pk}/"


@pytest.fixture(scope="module")
def contract():
    path = Path(__file__).resolve().parents[3] / "contracts/problems/openapi.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["components"]["schemas"]


@pytest.fixture
def problem():
    return ProblemFactory(status="error_conocido")


@pytest.fixture
def payload(problem):
    return {
        "problema_id": problem.pk,
        "titulo": "Certificado SMTP vencido",
        "descripcion": "El servidor SMTP rechaza conexiones TLS.",
        "causa_raiz": "El certificado TLS no se renueva automáticamente.",
        "workaround": "Renovar el certificado a mano y reiniciar el servicio de correo.",
    }


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert body["codigo"] == code
    assert isinstance(body["detalle"], str) and body["detalle"]
    assert set(body) <= {"codigo", "detalle", "campos"}
    return body


def result_ids(response):
    assert response.status_code == 200
    return [item["id"] for item in response.json()["results"]]


# --- List ----------------------------------------------------------------------------------------


def test_empty_list_returns_the_paginated_envelope(api):
    response = api.get(LIST_URL)
    assert response.status_code == 200
    assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}


def test_list_is_ordered_newest_first(api):
    oldest, newest, middle = KnownErrorFactory.create_batch(3)
    now = timezone.now()
    for known_error, hours in ((oldest, 3), (middle, 2), (newest, 1)):
        KnownError.objects.filter(pk=known_error.pk).update(created_at=now - timedelta(hours=hours))
    assert result_ids(api.get(LIST_URL)) == [newest.pk, middle.pk, oldest.pk]


def test_each_item_has_the_contract_fields_in_spanish(api, contract):
    known_error = KnownErrorFactory(kb_article_id="KB-128", is_active=False)
    item = api.get(LIST_URL).json()["results"][0]
    assert set(item) == set(contract["ErrorConocido"]["properties"])
    assert set(item) == set(contract["ErrorConocido"]["required"])
    assert item["problema_id"] == known_error.problem_id
    assert item["titulo"] == known_error.title
    assert item["causa_raiz"] == known_error.root_cause
    assert (item["articulo_kb_id"], item["activo"]) == ("KB-128", False)


def test_default_page_size_is_20_and_pages_can_be_followed(api):
    KnownErrorFactory.create_batch(25)
    first = api.get(LIST_URL).json()
    assert (first["count"], len(first["results"]), first["previous"]) == (25, 20, None)
    assert "page=2" in first["next"]
    second = api.get(LIST_URL, {"page": 2}).json()
    assert len(second["results"]) == 5
    assert second["next"] is None


def test_page_size_is_respected_and_capped_at_100(api):
    KnownErrorFactory.create_batch(101)
    assert len(api.get(LIST_URL, {"page_size": 7}).json()["results"]) == 7
    assert len(api.get(LIST_URL, {"page_size": 500}).json()["results"]) == 100


def test_out_of_range_page_is_404(api):
    KnownErrorFactory()
    body = assert_error(api.get(LIST_URL, {"page": 2}), 404, "no_encontrado")
    assert "campos" not in body


@pytest.mark.parametrize(("param", "value"), [("page", "0"), ("page", "x"), ("page_size", "0")])
def test_invalid_pagination_params_are_400(api, param, value):
    body = assert_error(api.get(LIST_URL, {param: value}), 400, "datos_invalidos")
    assert set(body["campos"]) == {param}


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("false", False)])
def test_filter_by_activo(api, value, expected):
    active = KnownErrorFactory(is_active=True)
    inactive = KnownErrorFactory(is_active=False)
    wanted = active if expected else inactive
    assert result_ids(api.get(LIST_URL, {"activo": value})) == [wanted.pk]


@pytest.mark.parametrize("value", ["", "si", "1", "True", "yes"])
def test_invalid_activo_is_400(api, value):
    body = assert_error(api.get(LIST_URL, {"activo": value}), 400, "datos_invalidos")
    assert body["campos"] == {"activo": f'"{value}" no es un booleano válido; usa true o false.'}


@pytest.mark.parametrize("field", ["title", "description", "root_cause", "workaround"])
def test_search_q_looks_in_each_text_field_ignoring_case(api, field):
    match = KnownErrorFactory(**{field: "Falla del servidor SMTP de pruebas"})
    KnownErrorFactory()
    assert result_ids(api.get(LIST_URL, {"q": "smtp"})) == [match.pk]
    assert result_ids(api.get(LIST_URL, {"q": "SMTP"})) == [match.pk]


def test_search_q_is_a_substring_match_and_trims_spaces(api):
    match = KnownErrorFactory(title="Certificado vencido")
    KnownErrorFactory(title="Disco lleno")
    assert result_ids(api.get(LIST_URL, {"q": "  ERTIFIC  "})) == [match.pk]


def test_search_q_matches_accented_text_ignoring_case(api):
    match = KnownErrorFactory(title="Caída del correo")
    KnownErrorFactory(title="Disco lleno")
    assert result_ids(api.get(LIST_URL, {"q": "CAÍDA"})) == [match.pk]


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_q_does_not_filter(api, value):
    KnownErrorFactory.create_batch(2)
    assert api.get(LIST_URL, {"q": value}).json()["count"] == 2


def test_search_q_without_matches_is_an_empty_page(api):
    KnownErrorFactory()
    assert api.get(LIST_URL, {"q": "no-existe"}).json()["results"] == []


def test_q_and_activo_can_be_combined_with_pagination(api):
    expected = KnownErrorFactory.create_batch(3, title="SMTP caído", is_active=True)
    KnownErrorFactory(title="SMTP lento", is_active=False)
    KnownErrorFactory(title="Disco lleno", is_active=True)
    body = api.get(LIST_URL, {"q": "smtp", "activo": "true", "page_size": 2}).json()
    assert body["count"] == 3
    assert {item["id"] for item in body["results"]} <= {k.pk for k in expected}
    assert "activo=true" in body["next"] and "q=smtp" in body["next"]


# --- Create --------------------------------------------------------------------------------------


def test_create_with_required_fields_applies_defaults(api, contract, payload, problem):
    response = api.post(LIST_URL, payload, format="json")
    assert response.status_code == 201
    body = response.json()
    assert set(body) == set(contract["ErrorConocido"]["properties"])
    assert {field: body[field] for field in payload} == payload
    assert (body["articulo_kb_id"], body["activo"]) == ("", True)
    known_error = KnownError.objects.get(pk=body["id"])
    assert known_error.problem_id == problem.pk
    assert known_error.root_cause == payload["causa_raiz"]
    assert list(problem.known_errors.all()) == [known_error]


def test_create_with_optional_fields(api, payload):
    payload |= {"articulo_kb_id": "KB-128", "activo": False}
    body = api.post(LIST_URL, payload, format="json").json()
    assert (body["articulo_kb_id"], body["activo"]) == ("KB-128", False)


def test_kb_article_id_is_stored_as_text_without_checking_knowledge(api, payload):
    payload["articulo_kb_id"] = "cualquier texto 123"
    response = api.post(LIST_URL, payload, format="json")
    assert response.status_code == 201
    assert response.json()["articulo_kb_id"] == "cualquier texto 123"


def test_create_ignores_read_only_fields(api, payload):
    payload |= {"id": 777, "creado_en": "2000-01-01T00:00:00Z", "actualizado_en": "2000-01-01"}
    body = api.post(LIST_URL, payload, format="json").json()
    assert body["id"] != 777
    assert not body["creado_en"].startswith("2000")
    assert not body["actualizado_en"].startswith("2000")


@pytest.mark.parametrize(
    "field", ["problema_id", "titulo", "descripcion", "causa_raiz", "workaround"]
)
def test_create_without_a_required_field_is_400(api, payload, field):
    del payload[field]
    body = assert_error(api.post(LIST_URL, payload, format="json"), 400, "datos_invalidos")
    assert body["campos"] == {field: "Este campo es requerido."}
    assert not KnownError.objects.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("titulo", ""),
        ("titulo", "x" * 201),
        ("descripcion", "   "),
        ("causa_raiz", ""),
        ("workaround", ""),
        ("articulo_kb_id", "k" * 65),
        ("activo", "talvez"),
        ("activo", None),
        ("problema_id", "abc"),
        ("problema_id", None),
    ],
)
def test_create_with_invalid_data_is_400(api, payload, field, value):
    payload[field] = value
    body = assert_error(api.post(LIST_URL, payload, format="json"), 400, "datos_invalidos")
    assert set(body["campos"]) == {field}
    assert isinstance(body["campos"][field], str)
    assert not KnownError.objects.exists()


@pytest.mark.parametrize("pk", [999999, 0])
def test_create_with_missing_problem_is_400_not_404(api, payload, pk):
    payload["problema_id"] = pk
    body = assert_error(api.post(LIST_URL, payload, format="json"), 400, "datos_invalidos")
    assert body["campos"] == {"problema_id": f"No existe el problema {pk}."}
    assert not KnownError.objects.exists()


def test_create_validation_error_format(api):
    body = api.post(LIST_URL, {}, format="json").json()
    assert body["codigo"] == "datos_invalidos"
    assert body["detalle"] == "La solicitud tiene campos inválidos."
    required = {"problema_id", "titulo", "descripcion", "causa_raiz", "workaround"}
    assert set(body["campos"]) == required


def test_create_with_malformed_json_is_400(api):
    response = api.generic("POST", LIST_URL, "{no es json", content_type="application/json")
    assert_error(response, 400, "datos_invalidos")


# --- Retrieve ------------------------------------------------------------------------------------


def test_retrieve_a_known_error(api, contract):
    known_error = KnownErrorFactory(kb_article_id="KB-9")
    response = api.get(detail_url(known_error.pk))
    assert response.status_code == 200
    body = response.json()
    assert set(body) == set(contract["ErrorConocido"]["properties"])
    assert (body["id"], body["problema_id"]) == (known_error.pk, known_error.problem_id)
    assert (body["workaround"], body["articulo_kb_id"]) == (known_error.workaround, "KB-9")


@pytest.mark.parametrize("pk", ["999999", "abc", "0"])
def test_retrieve_missing_known_error_is_404(api, pk):
    body = api.get(detail_url(pk)).json()
    assert body == {"codigo": "no_encontrado", "detalle": "No existe el recurso solicitado."}


# --- Partial update ------------------------------------------------------------------------------


def test_patch_updates_only_the_sent_fields(api):
    known_error = KnownErrorFactory()
    payload = {"articulo_kb_id": "KB-128", "activo": False}
    response = api.patch(detail_url(known_error.pk), payload, format="json")
    assert response.status_code == 200
    body = response.json()
    assert (body["articulo_kb_id"], body["activo"]) == ("KB-128", False)
    assert body["titulo"] == known_error.title
    known_error.refresh_from_db()
    assert (known_error.kb_article_id, known_error.is_active) == ("KB-128", False)


def test_patch_every_editable_field(api):
    known_error = KnownErrorFactory(kb_article_id="KB-1")
    payload = {
        "titulo": "Nuevo título",
        "descripcion": "Nueva descripción.",
        "causa_raiz": "Nueva causa.",
        "workaround": "Nuevo workaround.",
        "articulo_kb_id": "",
        "activo": True,
    }
    body = api.patch(detail_url(known_error.pk), payload, format="json").json()
    assert {field: body[field] for field in payload} == payload
    known_error.refresh_from_db()
    assert (known_error.title, known_error.root_cause) == ("Nuevo título", "Nueva causa.")
    assert known_error.kb_article_id == ""


def test_patch_updates_actualizado_en(api):
    known_error = KnownErrorFactory()
    before = known_error.updated_at
    api.patch(detail_url(known_error.pk), {"activo": False}, format="json")
    known_error.refresh_from_db()
    assert known_error.updated_at > before


def test_patch_cannot_move_a_known_error_to_another_problem(api):
    known_error = KnownErrorFactory()
    original = known_error.problem_id
    other = ProblemFactory()
    payload = {"problema_id": other.pk, "titulo": "Cambiado"}
    response = api.patch(detail_url(known_error.pk), payload, format="json")
    assert response.status_code == 200
    assert response.json()["problema_id"] == original
    assert response.json()["titulo"] == "Cambiado"
    known_error.refresh_from_db()
    assert known_error.problem_id == original
    assert not other.known_errors.exists()


def test_patch_ignores_read_only_fields(api):
    known_error = KnownErrorFactory()
    payload = {
        "id": 777,
        "creado_en": "2000-01-01T00:00:00Z",
        "actualizado_en": "2000-01-01T00:00:00Z",
        "activo": False,
    }
    body = api.patch(detail_url(known_error.pk), payload, format="json").json()
    assert body["id"] == known_error.pk
    assert not body["creado_en"].startswith("2000")
    assert not body["actualizado_en"].startswith("2000")
    assert KnownError.objects.filter(pk=known_error.pk, is_active=False).exists()


@pytest.mark.parametrize(
    "payload", [{}, None, {"problema_id": 1}, {"id": 5, "creado_en": "x"}, {"otro": "x"}]
)
def test_patch_without_editable_fields_is_400(api, payload):
    known_error = KnownErrorFactory()
    response = api.patch(detail_url(known_error.pk), payload, format="json")
    assert response.status_code == 400
    assert response.json() == {
        "codigo": "datos_invalidos",
        "detalle": "Envía al menos un campo modificable.",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("titulo", ""),
        ("titulo", None),
        ("descripcion", ""),
        ("causa_raiz", "   "),
        ("workaround", ""),
        ("articulo_kb_id", "k" * 65),
        ("activo", "talvez"),
    ],
)
def test_patch_with_invalid_data_is_400(api, field, value):
    known_error = KnownErrorFactory()
    response = api.patch(detail_url(known_error.pk), {field: value}, format="json")
    body = assert_error(response, 400, "datos_invalidos")
    assert set(body["campos"]) == {field}
    known_error.refresh_from_db()
    assert known_error.title.startswith("Error conocido")


@pytest.mark.parametrize("pk", ["999999", "abc"])
def test_patch_missing_known_error_is_404(api, pk):
    response = api.patch(detail_url(pk), {"activo": False}, format="json")
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
    ],
)
def test_methods_not_allowed_are_405(api, method, route):
    known_error = KnownErrorFactory()
    url = LIST_URL if route == "list" else detail_url(known_error.pk)
    response = getattr(api, method)(url, {"titulo": "X"}, format="json")
    body = assert_error(response, 405, "metodo_no_permitido")
    assert method.upper() in body["detalle"]
    assert KnownError.objects.filter(pk=known_error.pk, title=known_error.title).exists()
