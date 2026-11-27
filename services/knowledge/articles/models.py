"""Esquema de KB. Las identidades de Accesos son referencias, no FK.

Los identificadores de código están en inglés; ``verbose_name``, choices y mensajes siguen en
español. Los valores guardados (``"borrador"``, ``"empresa"``...) son los del contrato.
"""

import re
import uuid
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Category(models.Model):
    code = models.CharField(
        "código",
        max_length=50,
        primary_key=True,
        validators=[RegexValidator(r"\A[a-z][a-z0-9_]{0,49}\Z", "Usa un código en minúsculas.")],
    )
    name = models.CharField(
        "nombre",
        max_length=100,
        validators=[RegexValidator(r"\S", "Escribe un nombre no vacío.")],
    )
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField("creado en", default=timezone.now, editable=False)
    updated_at = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["name", "code"]
        constraints = [
            models.CheckConstraint(
                condition=Q(code__regex=r"^[a-z][a-z0-9_]{0,49}$"),
                name="kb_category_code_valid",
                violation_error_message="El código debe usar minúsculas, números o guion bajo.",
            ),
            models.CheckConstraint(
                condition=Q(name__regex=r"[^\s]"),
                name="kb_category_name_not_blank",
                violation_error_message="La categoría necesita un nombre no vacío.",
            ),
            models.CheckConstraint(
                condition=Q(updated_at__gte=F("created_at")),
                name="kb_category_dates_valid",
                violation_error_message="La actualización no puede preceder a la creación.",
            ),
        ]

    def __str__(self):
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "borrador", "Borrador"
        PUBLISHED = "publicado", "Publicado"
        ARCHIVED = "archivado", "Archivado"

    class Visibility(models.TextChoices):
        COMPANY = "empresa", "Usuarios de la empresa"
        SUPPORT = "soporte", "Solo soporte"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("título", max_length=200, blank=True, default="")
    content = models.TextField("contenido", blank=True, default="")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name="categoría",
    )
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(
        "visibilidad", max_length=16, choices=Visibility.choices, default=Visibility.SUPPORT
    )
    author_id = models.UUIDField(
        "ID del autor",
        null=True,
        blank=True,
        help_text="UUID externo de Accesos; no es el ID del usuario staff de este admin.",
    )
    created_at = models.DateTimeField("creado en", default=timezone.now, editable=False)
    updated_at = models.DateTimeField("actualizado en", auto_now=True)
    published_at = models.DateTimeField("publicado en", null=True, blank=True)
    archived_at = models.DateTimeField("archivado en", null=True, blank=True)

    class Meta:
        verbose_name = "artículo"
        verbose_name_plural = "artículos"
        ordering = ["-updated_at", "id"]
        indexes = [
            models.Index(
                fields=["status", "visibility", "-updated_at", "id"],
                name="kb_article_query_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["borrador", "publicado", "archivado"]),
                name="kb_article_status_valid",
                violation_error_message="El estado no está permitido.",
            ),
            models.CheckConstraint(
                condition=Q(visibility__in=["empresa", "soporte"]),
                name="kb_article_visibility_valid",
                violation_error_message="La visibilidad no está permitida.",
            ),
            models.CheckConstraint(
                condition=~Q(status="publicado")
                | (
                    Q(title__regex=r"[^\s]", content__regex=r"[^\s]")
                    & Q(category__isnull=False, author_id__isnull=False, published_at__isnull=False)
                ),
                name="kb_article_publication_complete",
                violation_error_message=(
                    "Para publicar completa título, contenido, categoría, autor y fecha."
                ),
            ),
            models.CheckConstraint(
                condition=(Q(status="archivado", archived_at__isnull=False))
                | (~Q(status="archivado") & Q(archived_at__isnull=True)),
                name="kb_article_archive_consistent",
                violation_error_message="La fecha de archivo corresponde solo al estado archivado.",
            ),
            models.CheckConstraint(
                condition=Q(updated_at__gte=F("created_at"))
                & (Q(published_at__isnull=True) | Q(published_at__gte=F("created_at")))
                & (Q(archived_at__isnull=True) | Q(archived_at__gte=F("created_at")))
                & (
                    Q(archived_at__isnull=True)
                    | Q(published_at__isnull=True)
                    | Q(archived_at__gte=F("published_at"))
                ),
                name="kb_article_dates_valid",
                violation_error_message=(
                    "Revisa el orden de las fechas de creación, publicación y archivo."
                ),
            ),
        ]

    def __str__(self):
        return self.title or f"Borrador {self.pk}"

    def clean(self):
        super().clean()
        errors = {}
        if self.status == self.Status.PUBLISHED:
            for field in ("title", "content", "category_id", "author_id", "published_at"):
                value = getattr(self, field)
                if not value or (isinstance(value, str) and not re.search(r"\S", value)):
                    errors["category" if field == "category_id" else field] = (
                        "Este dato es obligatorio para publicar."
                    )
            if (
                self.category_id
                and Category.objects.filter(pk=self.category_id, is_active=False).exists()
            ):
                errors["category"] = "Elige una categoría activa para publicar."
        if (self.status == self.Status.ARCHIVED) != (self.archived_at is not None):
            errors["archived_at"] = "Indica la fecha solo para un artículo archivado."
        for earlier, later in (
            ("created_at", "published_at"),
            ("created_at", "archived_at"),
            ("published_at", "archived_at"),
        ):
            start, end = getattr(self, earlier), getattr(self, later)
            if isinstance(start, datetime) and isinstance(end, datetime) and end < start:
                errors[later] = "Esta fecha no puede preceder a la anterior."
        if errors:
            raise ValidationError(errors)
