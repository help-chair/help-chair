from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
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


class ServicioSolicitableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServicioSolicitable.objects.filter(activo=True)
    serializer_class = ServicioSolicitableSerializer


class PeticionViewSet(viewsets.ModelViewSet):
    queryset = Peticion.objects.all()
    serializer_class = PeticionSerializer

    @extend_schema(request=CambioEstadoSerializer, responses=PeticionSerializer)
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

    @extend_schema(request=AsignarSerializer, responses=PeticionSerializer)
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