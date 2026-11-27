import uuid

import pytest
from django.urls import reverse

from articles.models import Article, Category

pytestmark = pytest.mark.django_db


def test_admin_saves_draft_without_using_staff_as_author(admin_client):
    response = admin_client.post(
        reverse("admin:articles_article_add"),
        {"title": "", "content": "", "status": "borrador", "visibility": "soporte"},
    )
    assert response.status_code == 302
    article = Article.objects.get()
    assert article.author_id is None
    delete_url = reverse("admin:articles_article_delete", args=[article.pk])
    assert admin_client.get(delete_url).status_code == 403


def test_admin_shows_errors_without_saving_incomplete_published(admin_client):
    article = Article.objects.create()
    response = admin_client.post(
        reverse("admin:articles_article_change", args=[article.pk]),
        {"title": " \t", "content": "", "status": "publicado", "visibility": "empresa"},
    )
    assert response.status_code == 200
    assert "title" in response.context["adminform"].form.errors
    article.refresh_from_db()
    assert article.status == "borrador"


def test_admin_requires_initial_draft_and_manages_dates_and_author(admin_client):
    category = Category.objects.create(code="red", name="Red")
    author = uuid.uuid4()
    data = {
        "title": "Ejemplo",
        "content": "Datos sintéticos",
        "category": category.pk,
        "author_id": str(author),
        "status": "publicado",
        "visibility": "empresa",
    }
    add_url = reverse("admin:articles_article_add")
    assert "status" in admin_client.post(add_url, data).context["adminform"].form.errors
    assert not Article.objects.exists()
    data["status"] = "borrador"
    assert admin_client.post(add_url, data).status_code == 302
    article = Article.objects.get()
    change_url = reverse("admin:articles_article_change", args=[article.pk])
    data.update(status="publicado", author_id=str(uuid.uuid4()), published_at_0="1900-01-01")
    assert admin_client.post(change_url, data).status_code == 302
    article.refresh_from_db()
    assert article.author_id == author  # El POST no puede sustituir el autor ya fijado.
    assert article.published_at >= article.created_at
    date = article.published_at
    data["status"] = "archivado"
    assert admin_client.post(change_url, data).status_code == 302
    article.refresh_from_db()
    assert article.published_at == date
    assert article.archived_at >= date


def test_admin_labels_stay_in_spanish(admin_client):
    response = admin_client.get(reverse("admin:articles_article_add"))
    form = response.context["adminform"].form
    assert form.fields["category"].label == "Categoría"
    assert form.fields["status"].label == "Estado"
    assert Category._meta.verbose_name_plural == "categorías"
    assert Article._meta.verbose_name_plural == "artículos"
