import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from articles.models import Article, Category

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return Category.objects.create(code="red", name="Red")


@pytest.fixture
def published(category):
    article = Article.objects.create()
    article.title = "Comprobar la conexión"
    article.content = "Contenido sintético de demostración."
    article.category = category
    article.author_id = uuid.uuid4()  # Sujeto externo: no se crea ningún usuario local.
    article.published_at = timezone.now()
    article.status = Article.Status.PUBLISHED
    article.full_clean()
    article.save()
    return article


def test_incomplete_draft_and_publication_with_external_reference(category):
    article = Article()
    article.full_clean()
    article.save()
    article.refresh_from_db()
    assert (article.title, article.content, article.category_id) == ("", "", None)
    assert article.status == Article.Status.DRAFT
    assert article.visibility == Article.Visibility.SUPPORT
    article.status = Article.Status.PUBLISHED
    with pytest.raises(ValidationError) as error:
        article.full_clean()
    assert {"title", "content", "category", "author_id", "published_at"} <= set(
        error.value.message_dict
    )


def test_choice_values_keep_the_contract_spanish_values():
    assert Article.Status.values == ["borrador", "publicado", "archivado"]
    assert Article.Visibility.values == ["empresa", "soporte"]


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        ({"status": "inventado"}, "kb_article_status_valid"),
        ({"visibility": "publico"}, "kb_article_visibility_valid"),
        ({"title": ""}, "kb_article_publication_complete"),
        ({"title": " \t\n"}, "kb_article_publication_complete"),
        ({"content": ""}, "kb_article_publication_complete"),
        ({"content": "\t\n"}, "kb_article_publication_complete"),
        ({"category_id": None}, "kb_article_publication_complete"),
        ({"author_id": None}, "kb_article_publication_complete"),
        ({"published_at": None}, "kb_article_publication_complete"),
        ({"status": "archivado"}, "kb_article_archive_consistent"),
    ],
)
def test_sql_rejects_invalid_published_rows_without_form_validation(published, changes, constraint):
    with pytest.raises(IntegrityError, match=constraint), transaction.atomic():
        Article.objects.filter(pk=published.pk).update(**changes)


@pytest.mark.parametrize(
    "case", ["published_before", "archived_before", "archived_without_status", "updated"]
)
def test_sql_rejects_inconsistent_dates_and_archive(published, case):
    before = published.created_at - timedelta(seconds=1)
    changes = {
        "published_before": {"published_at": before},
        "archived_before": {"status": "archivado", "archived_at": published.created_at},
        "archived_without_status": {"archived_at": timezone.now()},
        "updated": {"updated_at": before},
    }[case]
    constraint = (
        "kb_article_archive_consistent"
        if case == "archived_without_status"
        else "kb_article_dates_valid"
    )
    with pytest.raises(IntegrityError, match=constraint), transaction.atomic():
        Article.objects.filter(pk=published.pk).update(**changes)


@pytest.mark.parametrize("code", ["", "Red", "1red", "red-externa", "red\n", " red", "red "])
def test_invalid_category_code_in_validation_and_sql(code):
    with pytest.raises(ValidationError):
        Category(code=code, name="Red").full_clean()
    with pytest.raises(IntegrityError, match="kb_category_code_valid"), transaction.atomic():
        Category.objects.create(code=code, name="Red")


@pytest.mark.parametrize("name", ["", " \t\n"])
def test_category_name_not_blank_in_validation_and_sql(name):
    with pytest.raises(ValidationError):
        Category(code="red", name=name).full_clean()
    with pytest.raises(IntegrityError, match="kb_category_name_not_blank"), transaction.atomic():
        Category.objects.create(code="red", name=name)


def test_category_dates_constraint_in_sql():
    category = Category.objects.create(code="red", name="Red")
    before = category.created_at - timedelta(seconds=1)
    with pytest.raises(IntegrityError, match="kb_category_dates_valid"), transaction.atomic():
        Category.objects.filter(pk=category.pk).update(updated_at=before)


def test_local_fk_rejects_missing_category():
    with pytest.raises(IntegrityError), transaction.atomic():
        Article.objects.create(category_id="inexistente")
        # Las FK diferibles de PostgreSQL también deben comprobarse dentro del savepoint.
        connection.check_constraints()


@pytest.mark.parametrize("field,limit", [("code", 50), ("name", 100)])
def test_category_limits_in_validation_and_postgresql(field, limit):
    data = {"code": "red", "name": "Red", field: "a" * limit}
    category = Category(**data)
    category.full_clean()
    category.save()
    setattr(category, field, "a" * (limit + 1))
    with pytest.raises(ValidationError):
        category.full_clean()
    if connection.vendor == "postgresql":
        with pytest.raises(DataError), transaction.atomic():
            Category.objects.filter(pk=data["code"]).update(**{field: "a" * (limit + 1)})


def test_agreed_title_limit(published):
    published.title = "a" * 200
    published.full_clean()
    published.save()
    published.title += "a"
    with pytest.raises(ValidationError):
        published.full_clean()
    if connection.vendor == "postgresql":
        with pytest.raises(DataError), transaction.atomic():
            Article.objects.filter(pk=published.pk).update(title=published.title)


def test_archive_keeps_identity_and_category_is_protected(published):
    identity, content, date = published.pk, published.content, published.published_at
    with pytest.raises(ProtectedError):
        published.category.delete()
    published.status = Article.Status.ARCHIVED
    published.archived_at = timezone.now()
    published.full_clean()
    published.save()
    published.refresh_from_db()
    assert (published.pk, published.content, published.published_at) == (
        identity,
        content,
        date,
    )


def test_inactive_category_keeps_published_and_is_validated_on_publish(published):
    Category.objects.filter(pk=published.category_id).update(is_active=False)
    assert Article.objects.get(pk=published.pk).status == "publicado"
    with pytest.raises(ValidationError) as error:
        published.full_clean()
    assert "category" in error.value.message_dict


def test_equal_titles_do_not_become_an_unagreed_uniqueness(published):
    other = Article.objects.create(title=published.title)
    assert other.pk != published.pk


def test_related_name_lists_the_category_articles(published):
    assert list(published.category.articles.all()) == [published]


def test_invalid_dates_report_the_field_in_validation(published):
    published.published_at = published.created_at - timedelta(days=1)
    with pytest.raises(ValidationError) as error:
        published.full_clean()
    assert "published_at" in error.value.message_dict


def test_canonical_fixture_reloads_without_duplicates():
    from django.core.management import call_command

    call_command("loaddata", "kb_demo", verbosity=0)
    before = set(Article.objects.values_list("pk", flat=True))
    call_command("loaddata", "kb_demo", verbosity=0)
    assert Category.objects.count() == 2
    assert Article.objects.count() == 4
    assert set(Article.objects.values_list("pk", flat=True)) == before
    for article in Article.objects.all():
        article.full_clean()
