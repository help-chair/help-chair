"""POST /api/knowledge/v1/articulos/ (crearArticulo)."""

import pytest

from articles.models import Article
from tests.conftest import ARTICLES_URL, article_url
from tests.factories import CategoryFactory

pytestmark = pytest.mark.django_db

SERVER_MANAGED = {
    "id": "10900000-0000-4000-8000-000000000009",
    "estado": "publicado",
    "autor_id": "00000000-0000-4000-8000-000000000109",
    "creado_en": "2026-11-21T12:00:00Z",
    "actualizado_en": "2026-11-21T12:00:00Z",
    "publicado_en": "2026-11-21T12:00:00Z",
    "archivado_en": "2026-11-21T12:00:00Z",
}


def _post(api, body):
    return api.post(ARTICLES_URL, body, format="json")


def test_empty_body_creates_an_incomplete_draft(api, assert_contract_schema):
    response = _post(api, {})
    assert response.status_code == 201
    body = response.json()
    assert_contract_schema(body, "ArticuloBorrador")
    assert body["titulo"] == "" and body["contenido"] == ""
    assert body["categoria"] is None
    assert body["estado"] == "borrador"
    assert body["visibilidad"] == "soporte"
    # Sin JWT (D-29) no hay sub del que tomar el autor.
    assert body["autor_id"] is None
    assert body["publicado_en"] is None and body["archivado_en"] is None
    assert response["Location"] == article_url(body["id"])
    assert Article.objects.get(pk=body["id"]).status == Article.Status.DRAFT


def test_creates_a_draft_with_every_editable_field(api, assert_contract_schema):
    CategoryFactory(code="red")
    content = "  # Datos ficticios\n\n1. Paso con espacios finales  \n"
    response = _post(
        api,
        {"titulo": "Ejemplo", "contenido": content, "categoria": "red", "visibilidad": "empresa"},
    )
    assert response.status_code == 201
    body = response.json()
    assert_contract_schema(body, "ArticuloBorrador")
    assert (body["titulo"], body["contenido"], body["categoria"], body["visibilidad"]) == (
        "Ejemplo",
        content,
        "red",
        "empresa",
    )
    assert body["estado"] == "borrador"
    article = Article.objects.get(pk=body["id"])
    assert (article.title, article.content, article.category_id) == ("Ejemplo", content, "red")


def test_title_of_200_characters_is_accepted(api):
    response = _post(api, {"titulo": "a" * 200})
    assert response.status_code == 201


def test_explicit_null_category_is_accepted(api):
    response = _post(api, {"categoria": None})
    assert response.status_code == 201
    assert response.json()["categoria"] is None


def test_inactive_category_is_allowed_in_a_draft(api):
    # La categoría activa se exige al publicar (Article.clean), no en el borrador.
    CategoryFactory(code="antigua", is_active=False)
    assert _post(api, {"categoria": "antigua"}).status_code == 201


@pytest.mark.parametrize("field", sorted(SERVER_MANAGED))
def test_server_managed_fields_are_rejected(api, field, assert_contract_schema):
    response = _post(api, {"titulo": "Ejemplo", field: SERVER_MANAGED[field]})
    assert response.status_code == 400
    body = response.json()
    assert_contract_schema(body, "Error")
    assert body["campos"] == {field: "Lo asigna el servidor; no se puede enviar."}
    assert not Article.objects.exists()


@pytest.mark.parametrize("field", ["resumen", "title", "status", "empresa", "pasos"])
def test_unknown_fields_are_rejected(api, field):
    response = _post(api, {field: "x"})
    assert response.status_code == 400
    assert response.json()["campos"] == {field: "Campo no permitido."}
    assert not Article.objects.exists()


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"titulo": "a" * 201}, "titulo"),
        ({"titulo": None}, "titulo"),
        ({"titulo": 123}, "titulo"),
        ({"contenido": None}, "contenido"),
        ({"contenido": ["paso 1"]}, "contenido"),
        ({"visibilidad": "publico"}, "visibilidad"),
        ({"visibilidad": None}, "visibilidad"),
        ({"visibilidad": "Empresa"}, "visibilidad"),
        ({"categoria": "Red"}, "categoria"),
        ({"categoria": "red\n"}, "categoria"),
        ({"categoria": ""}, "categoria"),
        ({"categoria": 5}, "categoria"),
        ({"categoria": {"codigo": "red"}}, "categoria"),
    ],
)
def test_invalid_values_are_400(api, body, field, assert_contract_schema):
    CategoryFactory(code="red")
    response = _post(api, body)
    assert response.status_code == 400
    error = response.json()
    assert_contract_schema(error, "Error")
    assert error["codigo"] == "datos_invalidos"
    assert set(error["campos"]) == {field}
    assert not Article.objects.exists()


def test_missing_category_is_400(api):
    response = _post(api, {"categoria": "inexistente"})
    assert response.status_code == 400
    assert response.json()["campos"] == {"categoria": "No existe la categoría inexistente."}


@pytest.mark.parametrize("raw", ["[]", '["titulo"]', '"texto"', "5", "null", "true"])
def test_body_that_is_not_an_object_is_400(api, raw):
    response = api.post(ARTICLES_URL, raw, content_type="application/json")
    assert response.status_code == 400
    assert response.json()["codigo"] == "datos_invalidos"
    assert not Article.objects.exists()


def test_request_without_body_is_the_same_as_an_empty_object(api):
    response = api.post(ARTICLES_URL, content_type="application/json")
    assert response.status_code == 201
    assert response.json()["estado"] == "borrador"


def test_malformed_json_is_400(api):
    response = api.post(ARTICLES_URL, '{"titulo": ', content_type="application/json")
    assert response.status_code == 400
    assert response.json()["codigo"] == "datos_invalidos"


def test_non_json_body_is_415(api):
    response = api.post(ARTICLES_URL, {"titulo": "x"}, format="multipart")
    assert response.status_code == 415
    assert response.json()["codigo"] == "tipo_no_soportado"
    assert not Article.objects.exists()
