"""La API usa articles.access como único punto de autorización (provisional hasta D-29).

Simulan la política futura sustituyendo ese módulo: así se comprueba que la vista ya aplica la
audiencia antes de los filtros, responde 404 sin revelar lo no visible y toma el autor del
principal, sin implementar todavía la validación del JWT.
"""

import uuid

import pytest

from articles import access
from articles.models import Article
from tests.conftest import ARTICLES_URL, article_url
from tests.factories import ArticleFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def end_user_audience(monkeypatch):
    def published_for_company(request, queryset):
        return queryset.filter(
            status=Article.Status.PUBLISHED, visibility=Article.Visibility.COMPANY
        )

    monkeypatch.setattr("articles.views.visible_articles", published_for_company)


def test_today_every_request_sees_every_state_and_audience(api):
    for status in Article.Status.values:
        for visibility in Article.Visibility.values:
            ArticleFactory(status=status, visibility=visibility)
    assert api.get(ARTICLES_URL).json()["count"] == 6


def test_admin_session_does_not_authenticate_the_api(admin_client):
    response = admin_client.post(ARTICLES_URL, {}, content_type="application/json")
    assert response.status_code == 201
    # El usuario staff local nunca es el autor: el autor es un UUID externo de Accesos.
    assert response.json()["autor_id"] is None


def test_filters_cannot_widen_the_audience(api, end_user_audience):
    visible = ArticleFactory(status="publicado", visibility="empresa")
    ArticleFactory(status="publicado", visibility="soporte")
    ArticleFactory(status="borrador", visibility="empresa")
    assert [item["id"] for item in api.get(ARTICLES_URL).json()["results"]] == [str(visible.pk)]
    assert api.get(ARTICLES_URL, {"estado": "borrador"}).json()["count"] == 0


def test_an_article_outside_the_audience_is_404(api, end_user_audience):
    hidden = ArticleFactory(status="borrador", visibility="soporte")
    assert api.get(article_url(hidden.pk)).status_code == 404
    response = api.patch(article_url(hidden.pk), {"titulo": "x"}, format="json")
    assert response.status_code == 404
    hidden.refresh_from_db()
    assert hidden.title != "x"


def test_author_comes_from_the_principal_not_from_the_body(api, monkeypatch):
    author = uuid.uuid4()
    monkeypatch.setattr("articles.views.author_id_for", lambda request: author)
    response = api.post(ARTICLES_URL, {"titulo": "Con autor"}, format="json")
    assert response.status_code == 201
    assert response.json()["autor_id"] == str(author)


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", ARTICLES_URL),
        ("post", ARTICLES_URL),
        ("get", "detail"),
        ("patch", "detail"),
    ],
)
def test_a_denied_permission_is_403_no_permitido(api, monkeypatch, method, url):
    monkeypatch.setattr(access.ArticlePermission, "has_permission", lambda *args: False)
    article = ArticleFactory()
    target = article_url(article.pk) if url == "detail" else url
    response = getattr(api, method)(target, {"titulo": "x"}, format="json")
    assert response.status_code == 403
    assert response.json()["codigo"] == "no_permitido"
    assert Article.objects.count() == 1
