from rest_framework import viewsets

from .models import Peticion, ServicioSolicitable
from .serializers import PeticionSerializer, ServicioSolicitableSerializer


class ServicioSolicitableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServicioSolicitable.objects.filter(activo=True)
    serializer_class = ServicioSolicitableSerializer


class PeticionViewSet(viewsets.ModelViewSet):
    queryset = Peticion.objects.all()
    serializer_class = PeticionSerializer