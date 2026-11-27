"""GET /api/knowledge/v1/articulos/ (listarArticulos)."""

from datetime import timedelta

import pytest
from django.db import OperationalError
from django.utils import timezone
from jsonschema.exceptions import ValidationError as SchemaError

from articles.models import Article
from articles.views import ArticleViewSet
from tests.conftest import ARTICLES_URL
from tests.factories import ArticleFactory, CategoryFactory

pytestmark = pytest.mark.django_db

JSON_FIELDS = {
    "id",
    "titulo",
    "contenido",
    "categoria",
    "estado",
    "visibilidad",
    "autor_id",
    "creado_en",
    "actualizado_en",
    "publicado_en",
    "archivado_en",
}


def _ids(response):
    return [item["id"] for item in response.json()["results"]]


def _touch(article, updated_at):
    Article.objects.filter(pk=article.pk).update(updated_at=updated_at)


def test_empty_first_page_is_200_with_no_results(api, assert_contract_schema):
    response = api.get(ARTICLES_URL)
    assert response.status_code == 200
    assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}
    assert_contract_schema(response.json(), "PaginaArticulos")


def test_orders_by_last_update_descending_and_id_ascending(api):
    now = timezone.now()
    old, recent = ArticleFactory(), ArticleFactory()
    tie_a, tie_b = sorted([ArticleFactory(), ArticleFactory()], key=lambda a: str(a.pk))
    _touch(old, now + timedelta(minutes=1))
    _touch(recent, now + timedelta(minutes=3))
    _touch(tie_a, now + timedelta(minutes=2))
    _touch(tie_b, now + timedelta(minutes=2))
    assert _ids(api.get(ARTICLES_URL)) == [str(a.pk) for a in (recent, tie_a, tie_b, old)]


def test_items_have_exactly_the_contract_fields_for_every_state(api, assert_contract_schema):
    for status in Article.Status.values:
        ArticleFactory(status=status)
    body = api.get(ARTICLES_URL).json()
    assert body["count"] == 3
    for item in body["results"]:
        assert set(item) == JSON_FIELDS
    assert_contract_schema(body, "PaginaArticulos")


def test_the_contract_validator_rejects_extra_fields(assert_contract_schema):
    body = {"count": 0, "next": None, "previous": None, "results": [], "extra": 1}
    with pytest.raises(SchemaError):
        assert_contract_schema(body, "PaginaArticulos")


def test_paginates_with_page_and_page_size(api):
    articles = ArticleFactory.create_batch(5)
    first = api.get(ARTICLES_URL, {"page_size": 2}).json()
    assert first["count"] == 5
    assert len(first["results"]) == 2
    assert first["previous"] is None
    assert "page=2" in first["next"]
    last = api.get(ARTICLES_URL, {"page_size": 2, "page": 3}).json()
    assert len(last["results"]) == 1 and last["next"] is None
    seen = {
        item
        for page in (1, 2, 3)
        for item in _ids(api.get(ARTICLES_URL, {"page_size": 2, "page": page}))
    }
    assert seen == {str(a.pk) for a in articles}


def test_default_page_size_is_20_and_maximum_is_100(api):
    ArticleFactory.create_batch(101, category=CategoryFactory(code="red"))
    assert len(api.get(ARTICLES_URL).json()["results"]) == 20
    assert len(api.get(ARTICLES_URL, {"page_size": 500}).json()["results"]) == 100


def test_page_out_of_range_is_404(api):
    ArticleFactory()
    response = api.get(ARTICLES_URL, {"page": 2})
    assert response.status_code == 404
    assert response.json()["codigo"] == "no_encontrado"


@pytest.mark.parametrize(
    "params",
    [{"page": "0"}, {"page": "abc"}, {"page": "-1"}, {"page_size": "0"}, {"page_size": "x"}],
)
def test_invalid_pagination_is_400(api, params, assert_contract_schema):
    response = api.get(ARTICLES_URL, params)
    assert response.status_code == 400
    body = response.json()
    assert body["codigo"] == "datos_invalidos"
    assert set(body["campos"]) == set(params)
    assert_contract_schema(body, "Error")


@pytest.mark.parametrize("status", Article.Status.values)
def test_filters_by_status(api, status):
    expected = {str(ArticleFactory(status=value).pk): value for value in Article.Status.values}
    response = api.get(ARTICLES_URL, {"estado": status})
    assert response.status_code == 200
    assert [expected[pk] for pk in _ids(response)] == [status]


@pytest.mark.parametrize("value", ["", "Borrador", "publicada", "draft"])
def test_invalid_status_is_400(api, value):
    response = api.get(ARTICLES_URL, {"estado": value})
    assert response.status_code == 400
    assert "estado" in response.json()["campos"]


def test_filters_by_category_code(api):
    red = ArticleFactory(category=CategoryFactory(code="red"))
    ArticleFactory(category=CategoryFactory(code="software"))
    ArticleFactory(category=None)
    assert _ids(api.get(ARTICLES_URL, {"categoria": "red"})) == [str(red.pk)]


def test_unknown_category_returns_an_empty_list(api):
    ArticleFactory(category=CategoryFactory(code="red"))
    response = api.get(ARTICLES_URL, {"categoria": "inexistente"})
    assert response.status_code == 200
    assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}


@pytest.mark.parametrize("value", ["", "Red", "1red", "red-externa", "red\n", " red", "a" * 51])
def test_invalid_category_code_is_400(api, value):
    response = api.get(ARTICLES_URL, {"categoria": value})
    assert response.status_code == 400
    assert "categoria" in response.json()["campos"]


def test_combines_status_and_category(api):
    red = CategoryFactory(code="red")
    match = ArticleFactory(category=red, status=Article.Status.PUBLISHED)
    ArticleFactory(category=red)
    ArticleFactory(status=Article.Status.PUBLISHED)
    response = api.get(ARTICLES_URL, {"categoria": "red", "estado": "publicado"})
    assert _ids(response) == [str(match.pk)]


@pytest.mark.parametrize("value", ["conexión", "", " "])
def test_text_search_is_rejected_until_275(api, value):
    ArticleFactory()
    response = api.get(ARTICLES_URL, {"q": value})
    assert response.status_code == 400
    assert "#275" in response.json()["campos"]["q"]


def test_database_unavailable_is_503_without_internal_details(api, monkeypatch, caplog):
    def fail(self):
        raise OperationalError('connection to server at "db-secreta" failed for user "kb"')

    monkeypatch.setattr(ArticleViewSet, "get_queryset", fail)
    response = api.get(ARTICLES_URL)
    assert response.status_code == 503
    assert response.json() == {
        "codigo": "servicio_no_disponible",
        "detalle": "Servicio temporalmente no disponible.",
    }
    assert "db-secreta" not in response.content.decode()
    assert any(record.message == "database_unavailable" for record in caplog.records)


@pytest.mark.parametrize("method", ["put", "delete"])
def test_list_does_not_allow_put_or_delete(api, method):
    response = getattr(api, method)(ARTICLES_URL, {}, format="json")
    assert response.status_code == 405
    assert response.json()["codigo"] == "metodo_no_permitido"
