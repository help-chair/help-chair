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
        read_only_fields = [
            "id",
            "estado",
            "asignado_a_id",
            "motivo_cancelacion",
            "creada",
            "actualizada",
            "cerrada_en",
        ]

class CambioEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Peticion.Estado.choices)
    motivo_cancelacion = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )

    def validate(self, attrs):
        cancelando = attrs["estado"] == Peticion.Estado.CANCELADO
        if cancelando and not attrs.get("motivo_cancelacion"):
            raise serializers.ValidationError(
                {"motivo_cancelacion": "Es obligatorio al cancelar."}
            )
        return attrs


class AsignarSerializer(serializers.Serializer):
    asignado_a_id = serializers.IntegerField(min_value=1)