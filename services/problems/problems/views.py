"""API REST de problemas (contrato: contracts/problems/openapi.yaml, prefijo /api/problems/v1)."""

from django.db import transaction
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.filters import filter_by_choices
from core.schemas import INVALID_DATA, NOT_FOUND, PAGE_OUT_OF_RANGE, ErrorSerializer
from problems.models import Problema
from problems.serializers import (
    ProblemCreateSerializer,
    ProblemReadSerializer,
    ProblemUpdateSerializer,
    StateChangeSerializer,
)

LIST_FILTERS = {
    "estado": Problema.Estado,
    "prioridad": Problema.Prioridad,
    "origen": Problema.Origen,
}


# 401 se declarará cuando se valide el JWT de Accesos (Fase 3).
@extend_schema_view(
    list=extend_schema(
        operation_id="listProblemas",
        parameters=[
            OpenApiParameter(field, enum=choices.values) for field, choices in LIST_FILTERS.items()
        ],
        responses={200: ProblemReadSerializer, 400: INVALID_DATA, 404: PAGE_OUT_OF_RANGE},
    ),
    create=extend_schema(
        operation_id="createProblema",
        request=ProblemCreateSerializer,
        responses={201: ProblemReadSerializer, 400: INVALID_DATA},
    ),
    retrieve=extend_schema(
        operation_id="getProblema",
        responses={200: ProblemReadSerializer, 404: NOT_FOUND},
    ),
    partial_update=extend_schema(
        operation_id="updateProblema",
        request=ProblemUpdateSerializer,
        responses={200: ProblemReadSerializer, 400: INVALID_DATA, 404: NOT_FOUND},
    ),
    change_state=extend_schema(
        operation_id="changeProblemaEstado",
        request=StateChangeSerializer,
        responses={
            200: ProblemReadSerializer,
            400: INVALID_DATA,
            404: NOT_FOUND,
            409: OpenApiResponse(
                ErrorSerializer,
                description="Transición no permitida desde el estado actual",
                examples=[
                    OpenApiExample(
                        "transicion_invalida",
                        value={
                            "codigo": "transicion_invalida",
                            "detalle": "No se puede pasar de cerrado a en_analisis.",
                        },
                        response_only=True,
                        status_codes=["409"],
                    )
                ],
            ),
        },
    ),
)
class ProblemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Sin PUT ni DELETE: el router no los enruta y DRF responde 405."""

    queryset = Problema.objects.all()
    serializer_class = ProblemReadSerializer

    def get_queryset(self):
        queryset = Problema.objects.order_by("-creado_en", "-id")
        if self.action == "list":
            return filter_by_choices(queryset, self.request.query_params, LIST_FILTERS)
        if self.action == "change_state":
            # Bloquea la fila para que dos cambios simultáneos no partan del mismo estado.
            return queryset.select_for_update()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = ProblemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem = serializer.save()
        return Response(ProblemReadSerializer(problem).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        problem = self.get_object()
        serializer = ProblemUpdateSerializer(problem, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        problem = serializer.save()
        return Response(ProblemReadSerializer(problem).data)

    @action(detail=True, methods=["post"], url_path="estado")
    def change_state(self, request, *args, **kwargs):
        with transaction.atomic():
            problem = self.get_object()
            serializer = StateChangeSerializer(problem, data=request.data)
            serializer.is_valid(raise_exception=True)
            problem = serializer.save()
        return Response(ProblemReadSerializer(problem).data)
