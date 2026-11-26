"""Serializers de problemas, uno por esquema del contrato.

- ``ProblemReadSerializer``: lectura (``Problema``).
- ``ProblemCreateSerializer``: ``ProblemaCrear``; siempre crea en ``registrado``.
- ``ProblemUpdateSerializer``: ``ProblemaActualizar``; rechaza campos fuera del esquema.
- ``StateChangeSerializer``: ``CambioEstado``; aplica las reglas de ``problems.states``.

``component_name`` conserva en el esquema runtime los nombres de componente del contrato.
"""

from collections.abc import Mapping

from django.utils import timezone
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.settings import api_settings

from core.errors import Conflict
from problems import states
from problems.models import Problema


@extend_schema_serializer(component_name="Problema")
class ProblemReadSerializer(serializers.ModelSerializer):
    """Solo lectura: estado, resuelto_en y las fechas los controla el servicio."""

    class Meta:
        model = Problema
        fields = (
            "id",
            "titulo",
            "descripcion",
            "estado",
            "prioridad",
            "origen",
            "causa_raiz",
            "asignado_a_id",
            "creado_en",
            "actualizado_en",
            "resuelto_en",
        )
        read_only_fields = fields


@extend_schema_serializer(component_name="ProblemaCrear")
class ProblemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problema
        fields = ("titulo", "descripcion", "prioridad", "origen", "causa_raiz", "asignado_a_id")

    def create(self, validated_data):
        return Problema.objects.create(**validated_data, estado=Problema.Estado.REGISTRADO)


@extend_schema_serializer(component_name="ProblemaActualizar")
class ProblemUpdateSerializer(serializers.ModelSerializer):
    FORBIDDEN_FIELD_MESSAGES = {
        "estado": "El estado solo se cambia con POST /api/problems/v1/problemas/{id}/estado/.",
        "origen": "El origen no se puede modificar.",
    }

    class Meta:
        model = Problema
        fields = ("titulo", "descripcion", "prioridad", "causa_raiz", "asignado_a_id")

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            if not data:
                raise serializers.ValidationError(
                    {api_settings.NON_FIELD_ERRORS_KEY: "Envía al menos un campo."}
                )
            not_allowed = {
                field: self.FORBIDDEN_FIELD_MESSAGES.get(field, "Este campo no se puede modificar.")
                for field in data
                if field not in self.fields
            }
            if not_allowed:
                raise serializers.ValidationError(not_allowed)
        return super().to_internal_value(data)


@extend_schema_serializer(component_name="CambioEstado")
class StateChangeSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Problema.Estado.choices)
    causa_raiz = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        current, target = self.instance.estado, attrs["estado"]
        if not states.is_valid_transition(current, target):
            raise Conflict(
                states.invalid_transition_message(current, target),
                error_code="transicion_invalida",
            )
        root_cause = attrs.get("causa_raiz", self.instance.causa_raiz)
        if target in states.ROOT_CAUSE_REQUIRED_STATES and not root_cause.strip():
            raise serializers.ValidationError(
                {"causa_raiz": f"Se requiere la causa raíz para pasar a {target}."}
            )
        return attrs

    def update(self, instance, validated_data):
        target = validated_data["estado"]
        updated_fields = ["estado", "actualizado_en"]
        if target == Problema.Estado.RESUELTO:
            instance.resuelto_en = timezone.now()
            updated_fields.append("resuelto_en")
        elif states.is_reopening(instance.estado, target):
            instance.resuelto_en = None
            updated_fields.append("resuelto_en")
        if "causa_raiz" in validated_data:
            instance.causa_raiz = validated_data["causa_raiz"]
            updated_fields.append("causa_raiz")
        instance.estado = target
        instance.save(update_fields=updated_fields)
        return instance
