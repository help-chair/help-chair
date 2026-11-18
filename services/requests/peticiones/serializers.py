from rest_framework import serializers

from .models import Peticion, ServicioSolicitable


class ServicioSolicitableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioSolicitable
        fields = ["id", "nombre", "descripcion", "activo"]


class PeticionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Peticion
        fields = [
            "id",
            "tipo",
            "servicio",
            "titulo",
            "descripcion",
            "estado",
            "solicitante_id",
            "asignado_a_id",
            "evento_id",
            "motivo_cancelacion",
            "creada",
            "actualizada",
            "cerrada_en",
        ]
        read_only_fields = ["id", "creada", "actualizada", "cerrada_en"]