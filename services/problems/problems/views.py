"""API REST de problemas (contrato: contracts/problems/openapi.yaml, prefijo /api/problems/v1)."""

from django.db import IntegrityError, transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from core.errors import Conflict
from core.filters import filter_by_boolean, filter_by_choices, search_text
from core.schemas import INVALID_DATA, NOT_FOUND, PAGE_OUT_OF_RANGE, ErrorSerializer
from problems.models import KnownError, Problem, ProblemIncident
from problems.serializers import (
    IncidentLinkSerializer,
    KnownErrorCreateSerializer,
    KnownErrorReadSerializer,
    KnownErrorUpdateSerializer,
    ProblemCreateSerializer,
    ProblemIncidentReadSerializer,
    ProblemReadSerializer,
    ProblemUpdateSerializer,
    StateChangeSerializer,
)

# Parámetro del contrato -> (campo del modelo, opciones).
LIST_FILTERS = {
    "estado": ("status", Problem.Status),
    "prioridad": ("priority", Problem.Priority),
    "origen": ("origin", Problem.Origin),
}


# 401 se declarará cuando se valide el JWT de Accesos (Fase 3).
@extend_schema_view(
    list=extend_schema(
        operation_id="listProblemas",
        parameters=[
            OpenApiParameter(param, enum=choices.values)
            for param, (_, choices) in LIST_FILTERS.items()
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

    queryset = Problem.objects.all()
    serializer_class = ProblemReadSerializer

    def get_queryset(self):
        queryset = Problem.objects.order_by("-created_at", "-id")
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

    # --- Incidentes vinculados (#272) ------------------------------------------------------------

    @extend_schema(
        operation_id="listProblemaIncidentes",
        responses={200: ProblemIncidentReadSerializer(many=True), 404: NOT_FOUND},
    )
    @action(detail=True, methods=["get"], url_path="incidentes", pagination_class=None)
    def incidents(self, request, *args, **kwargs):
        """Arreglo sin paginar, del vínculo más antiguo al más reciente."""
        problem = self.get_object()
        links = problem.incidents.order_by("linked_at", "id")
        return Response(ProblemIncidentReadSerializer(links, many=True).data)

    @extend_schema(
        operation_id="linkProblemaIncidente",
        request=IncidentLinkSerializer,
        responses={
            201: ProblemIncidentReadSerializer,
            400: INVALID_DATA,
            404: NOT_FOUND,
            409: OpenApiResponse(
                ErrorSerializer,
                description="El incidente ya está vinculado a este problema",
                examples=[
                    OpenApiExample(
                        "incidente_ya_vinculado",
                        value={
                            "codigo": "incidente_ya_vinculado",
                            "detalle": "INC-1 ya está vinculado a PRB-42.",
                        },
                        response_only=True,
                        status_codes=["409"],
                    )
                ],
            ),
        },
    )
    @incidents.mapping.post
    def link_incident(self, request, *args, **kwargs):
        problem = self.get_object()
        serializer = IncidentLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident_id = serializer.validated_data["incident_id"]
        try:
            # El savepoint deja usable la transacción si la UniqueConstraint rechaza el alta.
            with transaction.atomic():
                link = ProblemIncident.objects.create(problem=problem, incident_id=incident_id)
        except IntegrityError:
            if not problem.incidents.filter(incident_id=incident_id).exists():
                raise
            raise Conflict(
                f"{incident_id} ya está vinculado a PRB-{problem.pk}.",
                error_code="incidente_ya_vinculado",
            ) from None
        return Response(ProblemIncidentReadSerializer(link).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="unlinkProblemaIncidente",
        parameters=[
            OpenApiParameter(
                "incidente_id",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                description="ID del incidente en el servicio de Incidencias",
            )
        ],
        request=None,
        responses={
            204: None,
            404: OpenApiResponse(
                ErrorSerializer,
                description="El problema no existe o el incidente no está vinculado a él",
            ),
        },
    )
    @action(
        detail=True,
        methods=["delete"],
        # Sin límite de longitud en la ruta: un ID que no existe da el 404 JSON, no el de Django.
        # El grupo se llama como el parámetro del contrato ({incidente_id}).
        url_path=r"incidentes/(?P<incidente_id>[^/]+)",
        pagination_class=None,
    )
    def unlink_incident(self, request, *args, **kwargs):
        incident_id = kwargs["incidente_id"]
        problem = self.get_object()
        deleted, _ = problem.incidents.filter(incident_id=incident_id).delete()
        if not deleted:
            raise NotFound(f"{incident_id} no está vinculado a PRB-{problem.pk}.")
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Errores conocidos (#273) --------------------------------------------------------------------

# Parámetro del contrato -> campo del modelo.
KNOWN_ERROR_BOOLEAN_FILTERS = {"activo": "is_active"}
# Campos en los que busca ``q`` (título, descripción, causa raíz y workaround).
KNOWN_ERROR_SEARCH_FIELDS = ("title", "description", "root_cause", "workaround")


# 401 se declarará cuando se valide el JWT de Accesos (Fase 3).
@extend_schema_view(
    list=extend_schema(
        operation_id="listErroresConocidos",
        parameters=[
            OpenApiParameter("activo", OpenApiTypes.BOOL),
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                description="Búsqueda por texto en título, descripción, causa raíz y workaround",
            ),
        ],
        responses={200: KnownErrorReadSerializer, 400: INVALID_DATA, 404: PAGE_OUT_OF_RANGE},
    ),
    create=extend_schema(
        operation_id="createErrorConocido",
        request=KnownErrorCreateSerializer,
        responses={
            201: KnownErrorReadSerializer,
            400: OpenApiResponse(
                ErrorSerializer, description="Datos inválidos o `problema_id` inexistente"
            ),
        },
    ),
    retrieve=extend_schema(
        operation_id="getErrorConocido",
        responses={200: KnownErrorReadSerializer, 404: NOT_FOUND},
    ),
    partial_update=extend_schema(
        operation_id="updateErrorConocido",
        request=KnownErrorUpdateSerializer,
        responses={200: KnownErrorReadSerializer, 400: INVALID_DATA, 404: NOT_FOUND},
    ),
)
class KnownErrorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Sin PUT ni DELETE: el router no los enruta y DRF responde 405."""

    queryset = KnownError.objects.all()
    serializer_class = KnownErrorReadSerializer

    def get_queryset(self):
        queryset = KnownError.objects.order_by("-created_at", "-id")
        if self.action == "list":
            params = self.request.query_params
            queryset = filter_by_boolean(queryset, params, KNOWN_ERROR_BOOLEAN_FILTERS)
            queryset = search_text(queryset, params, KNOWN_ERROR_SEARCH_FIELDS)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = KnownErrorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        known_error = serializer.save()
        return Response(KnownErrorReadSerializer(known_error).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        known_error = self.get_object()
        serializer = KnownErrorUpdateSerializer(known_error, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        known_error = serializer.save()
        return Response(KnownErrorReadSerializer(known_error).data)
