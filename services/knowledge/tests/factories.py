"""Factories de factory_boy para las pruebas de la API de artículos."""

import uuid

import factory
from django.utils import timezone

from articles.models import Article, Category

_PUBLISHED_ONCE = {Article.Status.PUBLISHED, Article.Status.ARCHIVED}


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"categoria_{n}")
    name = factory.LazyAttribute(lambda o: f"Categoría {o.code}")


class ArticleFactory(factory.django.DjangoModelFactory):
    """Artículo coherente con su estado: autor y fechas se derivan de ``status``.

    Un publicado o archivado cumple los CHECK de publicación completa y de fechas.
    """

    class Meta:
        model = Article

    title = factory.Sequence(lambda n: f"Artículo de prueba {n}")
    content = "Contenido sintético de prueba."
    category = factory.SubFactory(CategoryFactory)
    status = Article.Status.DRAFT
    visibility = Article.Visibility.SUPPORT
    # Se fija antes que las demás fechas para que publicación/archivo no la precedan.
    created_at = factory.LazyFunction(timezone.now)
    author_id = factory.LazyAttribute(
        lambda o: uuid.uuid4() if o.status in _PUBLISHED_ONCE else None
    )
    published_at = factory.LazyAttribute(
        lambda o: o.created_at if o.status in _PUBLISHED_ONCE else None
    )
    archived_at = factory.LazyAttribute(
        lambda o: o.created_at if o.status == Article.Status.ARCHIVED else None
    )
