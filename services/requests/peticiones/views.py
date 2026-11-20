from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Peticion, ServicioSolicitable
from .serializers import (
    AsignarSerializer,
    CambioEstadoSerializer,
    PeticionSerializer,
    ServicioSolicitableSerializer,
)

ESTADOS_ASIGNABLES = (
    Peticion.Estado.NUEVO,
    Peticion.Estado.ASIGNADO,
    Peticion.Estado.EN_PROCESO,
    Peticion.Estado.REABIERTO,
)

ERROR_400 = OpenApiResponse(description="Datos o parámetros de consulta inválidos.")
ERROR_404 = OpenApiResponse(description="Recurso no encontrado.")


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="incluir_inactivos",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Si es true, incluye servicios desactivados en el listado.",
            ),
        ],
        responses={200: ServicioSolicitableSerializer(many=True), 400: ERROR_400},
    ),
    create=extend_schema(responses={201: ServicioSolicitableSerializer, 400: ERROR_400}),
    retrieve=extend_schema(responses={200: ServicioSolicitableSerializer, 404: ERROR_404}),
    update=extend_schema(
        responses={200: ServicioSolicitableSerializer, 400: ERROR_400, 404: ERROR_404}
    ),
    partial_update=extend_schema(
        responses={200: ServicioSolicitableSerializer, 400: ERROR_400, 404: ERROR_404}
    ),
    destroy=extend_schema(responses={204: None, 404: ERROR_404}),
)
class ServicioSolicitableViewSet(viewsets.ModelViewSet):
    queryset = ServicioSolicitable.objects.all()
    serializer_class = ServicioSolicitableSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            raw = self.request.query_params.get("incluir_inactivos")
            if raw is None or raw == "":
                incluir_inactivos = False
            elif raw.lower() in ("true", "1"):
                incluir_inactivos = True
            elif raw.lower() in ("false", "0"):
                incluir_inactivos = False
            else:
                raise ValidationError(
                    {"incluir_inactivos": "Debe ser un booleano válido (true o false)."}
                )

            if not incluir_inactivos:
                qs = qs.filter(activo=True)
        return qs


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="estado",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[choice[0] for choice in Peticion.Estado.choices],
                description="Filtrar peticiones por estado.",
            ),
            OpenApiParameter(
                name="asignado_a_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtrar peticiones por ID del agente asignado.",
            ),
            OpenApiParameter(
                name="solicitante_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtrar peticiones por ID del usuario solicitante.",
            ),
        ],
        responses={200: PeticionSerializer(many=True), 400: ERROR_400},
    ),
    create=extend_schema(responses={201: PeticionSerializer, 400: ERROR_400}),
    retrieve=extend_schema(responses={200: PeticionSerializer, 404: ERROR_404}),
    update=extend_schema(responses={200: PeticionSerializer, 400: ERROR_400, 404: ERROR_404}),
    partial_update=extend_schema(
        responses={200: PeticionSerializer, 400: ERROR_400, 404: ERROR_404}
    ),
    destroy=extend_schema(responses={204: None, 404: ERROR_404}),
)
class PeticionViewSet(viewsets.ModelViewSet):
    queryset = Peticion.objects.all()
    serializer_class = PeticionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        estado = params.get("estado")
        if estado is not None and estado != "":
            if estado not in Peticion.Estado.values:
                raise ValidationError({"estado": "Estado no válido."})
            qs = qs.filter(estado=estado)

        for campo in ("asignado_a_id", "solicitante_id"):
            valor = params.get(campo)
            if valor is not None and valor != "":
                try:
                    qs = qs.filter(**{campo: int(valor)})
                except ValueError:
                    raise ValidationError({campo: "Debe ser un número entero válido."}) from None

        return qs

    @extend_schema(
        request=CambioEstadoSerializer,
        responses={200: PeticionSerializer, 400: ERROR_400, 404: ERROR_404},
    )
    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        peticion = self.get_object()
        entrada = CambioEstadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        nuevo = entrada.validated_data["estado"]

        if not peticion.puede_pasar_a(nuevo):
            return Response(
                {"detail": f"No se puede pasar de {peticion.estado} a {nuevo}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        peticion.estado = nuevo
        if nuevo == Peticion.Estado.CANCELADO:
            peticion.motivo_cancelacion = entrada.validated_data["motivo_cancelacion"]
        if nuevo == Peticion.Estado.CERRADO:
            peticion.cerrada_en = timezone.now()
        peticion.save()
        return Response(PeticionSerializer(peticion).data)

    @extend_schema(
        request=AsignarSerializer,
        responses={200: PeticionSerializer, 400: ERROR_400, 404: ERROR_404},
    )
    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        peticion = self.get_object()
        entrada = AsignarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        if peticion.estado not in ESTADOS_ASIGNABLES:
            return Response(
                {"detail": f"No se puede asignar en estado {peticion.estado}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        peticion.asignado_a_id = entrada.validated_data["asignado_a_id"]
        if peticion.estado in (Peticion.Estado.NUEVO, Peticion.Estado.REABIERTO):
            peticion.estado = Peticion.Estado.ASIGNADO
        peticion.save()
        return Response(PeticionSerializer(peticion).data)