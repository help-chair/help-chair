from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets

from .models import Incident, Status
from .priority import Priority
from .serializers import IncidentSerializer

FILTERS = [
    OpenApiParameter(
        "status", OpenApiTypes.STR, enum=Status.values, description="Filtra por estado."
    ),
    OpenApiParameter(
        "priority", OpenApiTypes.STR, enum=Priority.values, description="Filtra por prioridad."
    ),
    OpenApiParameter(
        "assigned_to", OpenApiTypes.STR, description="Filtra por ID del agente asignado."
    ),
]


@extend_schema_view(
    list=extend_schema(
        summary="Listar incidentes",
        description="Ordenados por prioridad (P1 primero) y luego del más reciente al más antiguo.",
        parameters=FILTERS,
    ),
    create=extend_schema(
        summary="Registrar un incidente",
        description="El incidente nace en estado «nuevo» y su prioridad se calcula con la "
        "matriz impacto × urgencia.",
    ),
    retrieve=extend_schema(summary="Ver un incidente"),
    partial_update=extend_schema(
        summary="Actualizar parcialmente un incidente",
        description="Sirve para asignar, cambiar impacto o urgencia (la prioridad se recalcula) "
        "o cambiar de estado siguiendo las transiciones permitidas.",
    ),
)
class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Incidentes (ITIL v4 · Incident Management). v0: sin autenticación (llega en la Fase 3)."""

    serializer_class = IncidentSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = Incident.objects.all()
        for field in ("status", "priority", "assigned_to"):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset
