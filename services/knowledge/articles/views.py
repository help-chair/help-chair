"""API REST de artículos (contrato: contracts/knowledge/openapi.yaml, prefijo /api/knowledge/v1).

Implementa listar, crear, consultar y editar borradores (#274). La búsqueda ``q`` y
``/soluciones/`` llegan en #275; la autorización por rol/audiencia vive en ``articles.access``.
"""

import uuid

from django.db import transaction
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from articles.access import ArticlePermission, author_id_for, visible_articles
from articles.models import Article
from articles.serializers import (
    CATEGORY_CODE,
    CATEGORY_CODE_MESSAGE,
    ArticleCreateSerializer,
    ArticleReadSerializer,
    ArticleUpdateSerializer,
)
from core.errors import Conflict
from core.filters import filter_by_choices, filter_by_pattern
from core.schemas import INVALID_DATA, NOT_EDITABLE, NOT_FOUND, UNAVAILABLE

STATUS_FILTERS = {"estado": ("status", Article.Status)}
CATEGORY_FILTERS = {"categoria": ("category_id", CATEGORY_CODE, CATEGORY_CODE_MESSAGE)}
# Parámetro del contrato que todavía no se implementa: llega con la búsqueda full-text (#275).
PENDING_SEARCH_PARAM = "q"

# Orden del contrato sin q: actualizado_en descendente, id ascendente.
ORDERING = ("-updated_at", "id")
# lookup_value_regex acepta cualquier segmento; el esquema documenta el UUID del contrato.
ARTICLE_ID = OpenApiParameter("id", OpenApiTypes.UUID, location=OpenApiParameter.PATH)


# 401 y 403 se declararán cuando se valide el JWT de Accesos (D-29, ver articles.access).
@extend_schema_view(
    list=extend_schema(
        operation_id="listarArticulos",
        summary="Listar artículos accesibles",
        parameters=[
            OpenApiParameter(
                "categoria",
                OpenApiTypes.STR,
                description="Código local de KB; un código desconocido devuelve lista vacía.",
                pattern=r"^[a-z][a-z0-9_]{0,49}$",
            ),
            OpenApiParameter("estado", OpenApiTypes.STR, enum=Article.Status.values),
        ],
        responses={
            200: ArticleReadSerializer,
            400: INVALID_DATA,
            404: NOT_FOUND,
            503: UNAVAILABLE,
        },
    ),
    create=extend_schema(
        operation_id="crearArticulo",
        summary="Crear un borrador",
        request=ArticleCreateSerializer,
        parameters=[
            OpenApiParameter(
                "Location",
                OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description="Ruta relativa del nuevo recurso.",
                response=[201],
            )
        ],
        responses={201: ArticleReadSerializer, 400: INVALID_DATA, 503: UNAVAILABLE},
    ),
    retrieve=extend_schema(
        operation_id="consultarArticulo",
        summary="Consultar un artículo por UUID",
        parameters=[ARTICLE_ID],
        responses={
            200: ArticleReadSerializer,
            400: INVALID_DATA,
            404: NOT_FOUND,
            503: UNAVAILABLE,
        },
    ),
    partial_update=extend_schema(
        operation_id="actualizarArticulo",
        summary="Editar campos de un borrador",
        parameters=[ARTICLE_ID],
        request=ArticleUpdateSerializer,
        responses={
            200: ArticleReadSerializer,
            400: INVALID_DATA,
            404: NOT_FOUND,
            409: NOT_EDITABLE,
            503: UNAVAILABLE,
        },
    ),
)
class ArticleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Sin PUT ni DELETE: el router no los enruta y DRF responde 405."""

    queryset = Article.objects.none()  # El esquema toma de aquí el tipo del id (UUID).
    serializer_class = ArticleReadSerializer
    permission_classes = [ArticlePermission]
    # Cualquier segmento llega a la vista: un id que no sea UUID es un 400, no un 404 de URL.
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        # La audiencia se aplica primero: ningún filtro posterior puede ampliarla.
        queryset = visible_articles(self.request, Article.objects.order_by(*ORDERING))
        if self.action == "list":
            return self._filter_list(queryset)
        if self.action == "partial_update":
            # Bloquea la fila: el borrador no puede cambiar de estado mientras se edita.
            return queryset.select_for_update()
        return queryset

    def _filter_list(self, queryset):
        params = self.request.query_params
        if PENDING_SEARCH_PARAM in params:
            raise ValidationError(
                {PENDING_SEARCH_PARAM: "La búsqueda por texto aún no está disponible (#275)."}
            )
        queryset = filter_by_choices(queryset, params, STATUS_FILTERS)
        return filter_by_pattern(queryset, params, CATEGORY_FILTERS)

    def get_object(self):
        value = self.kwargs[self.lookup_field]
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError({"id": "Debe ser un UUID válido."}) from None
        return super().get_object()

    def create(self, request, *args, **kwargs):
        serializer = ArticleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Nace siempre en borrador (el cuerpo no acepta estado) y con el autor del principal.
        article = serializer.save(author_id=author_id_for(request))
        location = reverse("article-detail", args=[article.pk])
        return Response(
            ArticleReadSerializer(article).data,
            status=status.HTTP_201_CREATED,
            headers={"Location": location},
        )

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            article = self.get_object()
            if article.status != Article.Status.DRAFT:
                raise Conflict(
                    "El artículo no es un borrador editable.", error_code="estado_no_editable"
                )
            serializer = ArticleUpdateSerializer(article, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            article = serializer.save()
        return Response(ArticleReadSerializer(article).data)
