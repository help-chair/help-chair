"""Serializers de la API de artículos (contrato: contracts/knowledge/openapi.yaml).

El JSON conserva los nombres del contrato en español y ``source=`` los mapea a los campos del
modelo en inglés. Lectura: ``ArticleReadSerializer`` (``Articulo``); escritura:
``ArticleCreateSerializer`` (``ArticuloCrear``) y ``ArticleUpdateSerializer``
(``ArticuloActualizar``). Los cuerpos de escritura rechazan campos desconocidos
(``additionalProperties: false``): estado, autor, identidad y fechas los gestiona el servidor.
"""

import re
from collections.abc import Mapping

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.settings import api_settings

from articles.models import Article, Category

# Nombre en el JSON -> campo del modelo.
ARTICLE_JSON_FIELDS = {
    "titulo": "title",
    "contenido": "content",
    "categoria": "category",
    "estado": "status",
    "visibilidad": "visibility",
    "autor_id": "author_id",
    "creado_en": "created_at",
    "actualizado_en": "updated_at",
    "publicado_en": "published_at",
    "archivado_en": "archived_at",
}
# Campos de lectura que el cliente nunca envía (los asigna el servidor).
SERVER_MANAGED_FIELDS = {"id", "estado", "autor_id"} | {
    name for name in ARTICLE_JSON_FIELDS if name.endswith("_en")
}
# Mismo patrón que Category.code y CodigoCategoria del contrato (fullmatch = final absoluto).
CATEGORY_CODE = re.compile(r"[a-z][a-z0-9_]{0,49}")
CATEGORY_CODE_MESSAGE = (
    "Usa un código de categoría en minúsculas: una letra y luego letras, números o guion bajo "
    "(máximo 50)."
)


def json_sources(fields: dict[str, str]) -> dict[str, dict[str, str]]:
    """``extra_kwargs`` con el ``source`` de cada campo cuyo nombre JSON difiere del modelo."""
    return {name: {"source": source} for name, source in fields.items() if name != source}


class StrictCharField(serializers.CharField):
    """Solo acepta texto JSON: DRF convertiría números en cadenas."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class CategoryCodeField(serializers.PrimaryKeyRelatedField):
    """Categoría por código local: distingue formato inválido de categoría inexistente."""

    default_error_messages = {
        "does_not_exist": "No existe la categoría {pk_value}.",
        "incorrect_type": "Debe ser el código de una categoría o null.",
        "invalid_code": CATEGORY_CODE_MESSAGE,
    }

    def run_validation(self, data=serializers.empty):
        # DRF convierte "" en null en los campos relacionales; aquí "" es un código inválido.
        if data == "":
            self.fail("invalid_code")
        return super().run_validation(data)

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("incorrect_type", data_type=type(data).__name__)
        if not CATEGORY_CODE.fullmatch(data):
            self.fail("invalid_code")
        return super().to_internal_value(data)


@extend_schema_serializer(component_name="Articulo")
class ArticleReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("id", *ARTICLE_JSON_FIELDS)
        read_only_fields = fields
        extra_kwargs = json_sources(ARTICLE_JSON_FIELDS)


class ArticleWriteSerializer(serializers.ModelSerializer):
    """Campos editables comunes a alta y edición; rechaza cualquier otro campo del cuerpo."""

    # Si es True, un cuerpo sin campos es un 400 (``minProperties: 1``).
    require_any_field = False

    # Se guardan tal cual: el contenido es Markdown y los espacios pueden ser significativos.
    titulo = StrictCharField(
        source="title", max_length=200, allow_blank=True, required=False, trim_whitespace=False
    )
    contenido = StrictCharField(
        source="content", allow_blank=True, required=False, trim_whitespace=False
    )
    categoria = CategoryCodeField(
        source="category", queryset=Category.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Article
        fields = ("titulo", "contenido", "categoria", "visibilidad")
        extra_kwargs = json_sources({"visibilidad": "visibility"})

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            if self.require_any_field and not data:
                raise serializers.ValidationError(
                    {api_settings.NON_FIELD_ERRORS_KEY: ["Envía al menos un campo editable."]}
                )
            unknown = {
                name: (
                    "Lo asigna el servidor; no se puede enviar."
                    if name in SERVER_MANAGED_FIELDS
                    else "Campo no permitido."
                )
                for name in data
                if name not in self.fields
            }
            if unknown:
                raise serializers.ValidationError(unknown)
        return super().to_internal_value(data)


@extend_schema_serializer(component_name="ArticuloCrear")
class ArticleCreateSerializer(ArticleWriteSerializer):
    """Alta de un borrador; un cuerpo vacío crea un borrador incompleto."""


@extend_schema_serializer(component_name="ArticuloActualizar")
class ArticleUpdateSerializer(ArticleWriteSerializer):
    """Edición parcial de un borrador; ``categoria: null`` quita la categoría."""

    require_any_field = True
