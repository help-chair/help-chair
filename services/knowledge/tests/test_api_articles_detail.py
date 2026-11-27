"""GET y PATCH /api/knowledge/v1/articulos/{id}/ (consultarArticulo, actualizarArticulo)."""

import uuid

import pytest
from django.core.management import call_command

from articles.models import Article
from tests.conftest import article_url
from tests.factories import ArticleFactory, CategoryFactory

pytestmark = pytest.mark.django_db

# Ejemplos del contrato que reproducen la fixture canónica kb_demo.json.
FIXTURE_EXAMPLES = {
    "10900000-0000-4000-8000-000000000001": "Borrador",
    "10900000-0000-4000-8000-000000000002": "PublicadoEmpresa",
    "10900000-0000-4000-8000-000000000003": "PublicadoSoporte",
    "10900000-0000-4000-8000-000000000004": "Archivado",
}
INVALID_IDS = ["abc", "KB-028", "10900000-0000-4000-8000-00000000000", "1"]


def _patch(api, pk, body):
    return api.patch(article_url(pk), body, format="json")


def _snapshot(article):
    article.refresh_from_db()
    return {field.name: getattr(article, field.attname) for field in Article._meta.concrete_fields}


# --- GET -----------------------------------------------------------------------------------


@pytest.mark.parametrize(("pk", "example"), FIXTURE_EXAMPLES.items())
def test_get_returns_exactly_the_contract_example(api, contract, pk, example):
    call_command("loaddata", "kb_demo", verbosity=0)
    response = api.get(article_url(pk))
    assert response.status_code == 200
    assert response.json() == contract["components"]["examples"][example]["value"]


@pytest.mark.parametrize("status", Article.Status.values)
def test_get_matches_the_contract_schema_in_every_state(api, status, assert_contract_schema):
    article = ArticleFactory(status=status)
    response = api.get(article_url(article.pk))
    assert response.status_code == 200
    assert_contract_schema(response.json(), "Articulo")


def test_get_missing_article_is_404(api, assert_contract_schema):
    response = api.get(article_url(uuid.uuid4()))
    assert response.status_code == 404
    assert response.json() == {"codigo": "no_encontrado", "detalle": "Recurso no encontrado."}
    assert_contract_schema(response.json(), "Error")


@pytest.mark.parametrize("pk", INVALID_IDS)
def test_get_with_an_invalid_uuid_is_400(api, pk):
    response = api.get(article_url(pk))
    assert response.status_code == 400
    assert response.json()["campos"] == {"id": "Debe ser un UUID válido."}


@pytest.mark.parametrize("method", ["put", "delete", "post"])
def test_detail_does_not_allow_put_delete_or_post(api, method):
    article = ArticleFactory()
    response = getattr(api, method)(article_url(article.pk), {}, format="json")
    assert response.status_code == 405
    assert Article.objects.filter(pk=article.pk).exists()


# --- PATCH ---------------------------------------------------------------------------------


def test_patch_updates_only_the_fields_sent(api, assert_contract_schema):
    article = ArticleFactory(title="Antes", content="Contenido", visibility="soporte")
    before = _snapshot(article)
    response = _patch(api, article.pk, {"titulo": "Borrador de demostración"})
    assert response.status_code == 200
    body = response.json()
    assert_contract_schema(body, "ArticuloBorrador")
    after = _snapshot(article)
    assert after["title"] == body["titulo"] == "Borrador de demostración"
    unchanged = {"content", "category", "visibility", "status", "author_id", "created_at"}
    assert {name: after[name] for name in unchanged} == {name: before[name] for name in unchanged}
    assert after["updated_at"] > before["updated_at"]


def test_patch_can_update_every_editable_field(api):
    CategoryFactory(code="software")
    article = ArticleFactory()
    content = "Paso 1\n\n  Paso 2  "
    body = {
        "titulo": "Nuevo",
        "contenido": content,
        "categoria": "software",
        "visibilidad": "empresa",
    }
    response = _patch(api, article.pk, body)
    assert response.status_code == 200
    assert {name: response.json()[name] for name in body} == body
    article.refresh_from_db()
    assert (article.title, article.content, article.category_id, article.visibility) == (
        "Nuevo",
        content,
        "software",
        "empresa",
    )


def test_patch_with_null_category_removes_it(api):
    article = ArticleFactory(category=CategoryFactory(code="red"))
    response = _patch(api, article.pk, {"categoria": None})
    assert response.status_code == 200
    assert response.json()["categoria"] is None
    article.refresh_from_db()
    assert article.category_id is None


def test_patch_with_empty_strings_keeps_an_incomplete_draft(api):
    article = ArticleFactory()
    response = _patch(api, article.pk, {"titulo": "", "contenido": ""})
    assert response.status_code == 200
    assert (response.json()["titulo"], response.json()["contenido"]) == ("", "")


def test_patch_with_empty_body_is_400(api):
    article = ArticleFactory()
    before = _snapshot(article)
    response = _patch(api, article.pk, {})
    assert response.status_code == 400
    assert response.json() == {
        "codigo": "datos_invalidos",
        "detalle": "Envía al menos un campo editable.",
    }
    assert _snapshot(article) == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("estado", "publicado"),
        ("estado", "archivado"),
        ("autor_id", "00000000-0000-4000-8000-000000000109"),
        ("id", "10900000-0000-4000-8000-000000000009"),
        ("creado_en", "2026-11-21T12:00:00Z"),
        ("actualizado_en", "2026-11-21T12:00:00Z"),
        ("publicado_en", "2026-11-21T12:00:00Z"),
        ("archivado_en", "2026-11-21T12:00:00Z"),
    ],
)
def test_patch_cannot_change_server_managed_fields(api, field, value):
    article = ArticleFactory()
    before = _snapshot(article)
    response = _patch(api, article.pk, {"titulo": "Cambio", field: value})
    assert response.status_code == 400
    assert response.json()["campos"] == {field: "Lo asigna el servidor; no se puede enviar."}
    assert _snapshot(article) == before


def test_patch_rejects_unknown_fields(api):
    article = ArticleFactory()
    response = _patch(api, article.pk, {"resumen": "x"})
    assert response.status_code == 400
    assert response.json()["campos"] == {"resumen": "Campo no permitido."}


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"titulo": "a" * 201}, "titulo"),
        ({"titulo": None}, "titulo"),
        ({"contenido": 7}, "contenido"),
        ({"visibilidad": "publico"}, "visibilidad"),
        ({"categoria": "Red"}, "categoria"),
        ({"categoria": "inexistente"}, "categoria"),
    ],
)
def test_patch_with_invalid_values_is_400_and_changes_nothing(api, body, field):
    article = ArticleFactory()
    before = _snapshot(article)
    response = _patch(api, article.pk, body)
    assert response.status_code == 400
    assert set(response.json()["campos"]) == {field}
    assert _snapshot(article) == before


@pytest.mark.parametrize("status", [Article.Status.PUBLISHED, Article.Status.ARCHIVED])
@pytest.mark.parametrize("body", [{"titulo": "Cambio"}, {}, {"estado": "borrador"}])
def test_patch_on_a_non_draft_is_409(api, status, body, assert_contract_schema):
    article = ArticleFactory(status=status)
    before = _snapshot(article)
    response = _patch(api, article.pk, body)
    assert response.status_code == 409
    assert response.json() == {
        "codigo": "estado_no_editable",
        "detalle": "El artículo no es un borrador editable.",
    }
    assert_contract_schema(response.json(), "Error")
    assert _snapshot(article) == before


def test_patch_missing_article_is_404(api):
    response = _patch(api, uuid.uuid4(), {"titulo": "x"})
    assert response.status_code == 404
    assert response.json()["codigo"] == "no_encontrado"


@pytest.mark.parametrize("pk", INVALID_IDS)
def test_patch_with_an_invalid_uuid_is_400(api, pk):
    response = _patch(api, pk, {"titulo": "x"})
    assert response.status_code == 400
    assert response.json()["campos"] == {"id": "Debe ser un UUID válido."}
