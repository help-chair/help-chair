"""Esquema inicial de KB. Las identidades de Accesos son referencias, no FK."""

import re
import uuid
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Categoria(models.Model):
    codigo = models.CharField(
        max_length=50,
        primary_key=True,
        validators=[RegexValidator(r"\A[a-z][a-z0-9_]{0,49}\Z", "Usa un código en minúsculas.")],
    )
    nombre = models.CharField(
        max_length=100, validators=[RegexValidator(r"\S", "Escribe un nombre no vacío.")]
    )
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre", "codigo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(codigo__regex=r"^[a-z][a-z0-9_]{0,49}$"),
                name="kb_categoria_codigo_valido",
                violation_error_message="El código debe usar minúsculas, números o guion bajo.",
            ),
            models.CheckConstraint(
                condition=Q(nombre__regex=r"[^\s]"),
                name="kb_categoria_nombre_no_blanco",
                violation_error_message="La categoría necesita un nombre no vacío.",
            ),
            models.CheckConstraint(
                condition=Q(actualizado_en__gte=F("creado_en")),
                name="kb_categoria_fechas_validas",
                violation_error_message="La actualización no puede preceder a la creación.",
            ),
        ]

    def __str__(self):
        return self.nombre


class Articulo(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PUBLICADO = "publicado", "Publicado"
        ARCHIVADO = "archivado", "Archivado"

    class Visibilidad(models.TextChoices):
        EMPRESA = "empresa", "Usuarios de la empresa"
        SOPORTE = "soporte", "Solo soporte"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField("título", max_length=200, blank=True, default="")
    contenido = models.TextField(blank=True, default="")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, null=True, blank=True, related_name="articulos"
    )
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.BORRADOR)
    visibilidad = models.CharField(
        max_length=16, choices=Visibilidad.choices, default=Visibilidad.SOPORTE
    )
    autor_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID externo de Accesos; no es el ID del usuario staff de este admin.",
    )
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True)
    publicado_en = models.DateTimeField(null=True, blank=True)
    archivado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "artículo"
        ordering = ["-actualizado_en", "id"]
        indexes = [
            models.Index(
                fields=["estado", "visibilidad", "-actualizado_en", "id"],
                name="kb_articulo_consulta_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=["borrador", "publicado", "archivado"]),
                name="kb_articulo_estado_valido",
                violation_error_message="El estado no está permitido.",
            ),
            models.CheckConstraint(
                condition=Q(visibilidad__in=["empresa", "soporte"]),
                name="kb_articulo_visibilidad_valida",
                violation_error_message="La visibilidad no está permitida.",
            ),
            models.CheckConstraint(
                condition=~Q(estado="publicado")
                | (
                    Q(titulo__regex=r"[^\s]", contenido__regex=r"[^\s]")
                    & Q(categoria__isnull=False, autor_id__isnull=False, publicado_en__isnull=False)
                ),
                name="kb_articulo_publicacion_completa",
                violation_error_message=(
                    "Para publicar completa título, contenido, categoría, autor y fecha."
                ),
            ),
            models.CheckConstraint(
                condition=(Q(estado="archivado", archivado_en__isnull=False))
                | (~Q(estado="archivado") & Q(archivado_en__isnull=True)),
                name="kb_articulo_archivo_consistente",
                violation_error_message="La fecha de archivo corresponde solo al estado archivado.",
            ),
            models.CheckConstraint(
                condition=Q(actualizado_en__gte=F("creado_en"))
                & (Q(publicado_en__isnull=True) | Q(publicado_en__gte=F("creado_en")))
                & (Q(archivado_en__isnull=True) | Q(archivado_en__gte=F("creado_en")))
                & (
                    Q(archivado_en__isnull=True)
                    | Q(publicado_en__isnull=True)
                    | Q(archivado_en__gte=F("publicado_en"))
                ),
                name="kb_articulo_fechas_validas",
                violation_error_message=(
                    "Revisa el orden de las fechas de creación, publicación y archivo."
                ),
            ),
        ]

    def __str__(self):
        return self.titulo or f"Borrador {self.pk}"

    def clean(self):
        super().clean()
        errores = {}
        if self.estado == self.Estado.PUBLICADO:
            for campo in ("titulo", "contenido", "categoria_id", "autor_id", "publicado_en"):
                valor = getattr(self, campo)
                if not valor or (isinstance(valor, str) and not re.search(r"\S", valor)):
                    errores["categoria" if campo == "categoria_id" else campo] = (
                        "Este dato es obligatorio para publicar."
                    )
            if (
                self.categoria_id
                and Categoria.objects.filter(pk=self.categoria_id, activa=False).exists()
            ):
                errores["categoria"] = "Elige una categoría activa para publicar."
        if (self.estado == self.Estado.ARCHIVADO) != (self.archivado_en is not None):
            errores["archivado_en"] = "Indica la fecha solo para un artículo archivado."
        for anterior, posterior in (
            ("creado_en", "publicado_en"),
            ("creado_en", "archivado_en"),
            ("publicado_en", "archivado_en"),
        ):
            inicio, fin = getattr(self, anterior), getattr(self, posterior)
            if isinstance(inicio, datetime) and isinstance(fin, datetime) and fin < inicio:
                errores[posterior] = "Esta fecha no puede preceder a la anterior."
        if errores:
            raise ValidationError(errores)
