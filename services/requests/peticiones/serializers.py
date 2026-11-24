from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import CatalogItem, ServiceRequest


class CatalogItemSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(
        source="name",
        max_length=120,
        validators=[
            UniqueValidator(
                queryset=CatalogItem.objects.all(),
                message="Ya existe un servicio con este nombre.",
            )
        ],
    )
    descripcion = serializers.CharField(
        source="description", required=False, allow_blank=True, default=""
    )
    activo = serializers.BooleanField(source="is_active", required=False, default=True)
    creado_en = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = CatalogItem
        fields = ["id", "nombre", "descripcion", "activo", "creado_en"]
        read_only_fields = ["id", "creado_en"]


class ServiceRequestSerializer(serializers.ModelSerializer):
    tipo = serializers.ChoiceField(
        source="request_type",
        choices=ServiceRequest.RequestType.choices,
        default=ServiceRequest.RequestType.SERVICE,
        required=False,
    )
    servicio = serializers.PrimaryKeyRelatedField(
        source="service", queryset=CatalogItem.objects.all()
    )
    titulo = serializers.CharField(source="title", max_length=150)
    descripcion = serializers.CharField(
        source="description", required=False, allow_blank=True
    )
    estado = serializers.CharField(source="status", read_only=True)
    estado_aprobacion = serializers.CharField(source="approval_status", read_only=True)
    aprobador_id = serializers.IntegerField(
        source="approver_id", required=False, allow_null=True, min_value=1
    )
    aprobada_en = serializers.DateTimeField(source="approved_at", read_only=True)
    motivo_rechazo = serializers.CharField(source="rejection_reason", read_only=True)
    solicitante_id = serializers.IntegerField(source="requester_id", min_value=0)
    asignado_a_id = serializers.IntegerField(source="assignee_id", read_only=True)
    evento_id = serializers.CharField(
        source="event_id", required=False, allow_blank=True, default="", max_length=64
    )
    motivo_cancelacion = serializers.CharField(
        source="cancellation_reason", read_only=True
    )
    creada = serializers.DateTimeField(source="created_at", read_only=True)
    actualizada = serializers.DateTimeField(source="updated_at", read_only=True)
    cerrada_en = serializers.DateTimeField(source="closed_at", read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "tipo",
            "servicio",
            "titulo",
            "descripcion",
            "estado",
            "estado_aprobacion",
            "aprobador_id",
            "aprobada_en",
            "motivo_rechazo",
            "solicitante_id",
            "asignado_a_id",
            "evento_id",
            "motivo_cancelacion",
            "creada",
            "actualizada",
            "cerrada_en",
        ]

    def validate_servicio(self, service_item: CatalogItem) -> CatalogItem:
        if not service_item.is_active:
            raise serializers.ValidationError("El servicio seleccionado no está activo.")
        return service_item

    def create(self, validated_data):
        request_type = validated_data.get(
            "request_type", ServiceRequest.RequestType.SERVICE
        )
        if request_type == ServiceRequest.RequestType.CHANGE:
            validated_data["approval_status"] = ServiceRequest.ApprovalStatus.PENDING
        else:
            validated_data["approval_status"] = ServiceRequest.ApprovalStatus.NOT_REQUIRED
        return super().create(validated_data)


class StatusChangeSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=ServiceRequest.Status.choices)
    motivo_cancelacion = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )

    def validate(self, attrs):
        is_cancelling = attrs["estado"] == ServiceRequest.Status.CANCELLED
        if is_cancelling and not attrs.get("motivo_cancelacion"):
            raise serializers.ValidationError(
                {"motivo_cancelacion": "Es obligatorio al cancelar."}
            )
        return attrs


class AssignRequestSerializer(serializers.Serializer):
    asignado_a_id = serializers.IntegerField(min_value=1)


class ApproveChangeSerializer(serializers.Serializer):
    aprobador_id = serializers.IntegerField(min_value=1)


class RejectChangeSerializer(serializers.Serializer):
    aprobador_id = serializers.IntegerField(min_value=1)
    motivo_rechazo = serializers.CharField(max_length=255)