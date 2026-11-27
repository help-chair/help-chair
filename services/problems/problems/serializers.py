"""Serializers de problemas, uno por esquema del contrato.

- ``ProblemReadSerializer``: lectura (``Problema``).
- ``ProblemCreateSerializer``: ``ProblemaCrear``; siempre crea en ``registrado``.
- ``ProblemUpdateSerializer``: ``ProblemaActualizar``; rechaza campos fuera del esquema.
- ``StateChangeSerializer``: ``CambioEstado``; aplica las reglas de ``problems.states``.
- ``ProblemIncidentReadSerializer``: lectura (``ProblemaIncidente``).
- ``IncidentLinkSerializer``: ``VincularIncidente``; solo valida ``incidente_id``.
- ``KnownErrorReadSerializer``: lectura (``ErrorConocido``).
- ``KnownErrorCreateSerializer``: ``ErrorConocidoCrear``; ``problema_id`` inexistente es 400.
- ``KnownErrorUpdateSerializer``: ``ErrorConocidoActualizar``; ignora los de solo lectura.

``component_name`` conserva en el esquema runtime los nombres de componente del contrato, y
``source=`` mapea cada nombre del JSON (español, del contrato) al campo del modelo (inglés).
"""

from collections.abc import Mapping

from django.utils import timezone
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.settings import api_settings

from core.errors import Conflict
from problems import states
from problems.models import KnownError, Problem, ProblemIncident

# Nombre en el JSON del contrato -> campo del modelo. El contrato no cambia: solo el código.
PROBLEM_JSON_FIELDS = {
    "titulo": "title",
    "descripcion": "description",
    "estado": "status",
    "prioridad": "priority",
    "origen": "origin",
    "causa_raiz": "root_cause",
    "asignado_a_id": "assignee_id",
    "creado_en": "created_at",
    "actualizado_en": "updated_at",
    "resuelto_en": "resolved_at",
}


def json_sources(*names):
    """``extra_kwargs`` que mapean cada nombre del JSON a su campo del modelo."""
    return {name: {"source": PROBLEM_JSON_FIELDS[name]} for name in names}


@extend_schema_serializer(component_name="Problema")
class ProblemReadSerializer(serializers.ModelSerializer):
    """Solo lectura: estado, resuelto_en y las fechas los controla el servicio."""

    class Meta:
        model = Problem
        fields = ("id", *PROBLEM_JSON_FIELDS)
        read_only_fields = fields
        extra_kwargs = json_sources(*PROBLEM_JSON_FIELDS)


@extend_schema_serializer(component_name="ProblemaCrear")
class ProblemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ("titulo", "descripcion", "prioridad", "origen", "causa_raiz", "asignado_a_id")
        extra_kwargs = json_sources(*fields)

    def create(self, validated_data):
        return Problem.objects.create(**validated_data, status=Problem.Status.REGISTERED)


@extend_schema_serializer(component_name="ProblemaActualizar")
class ProblemUpdateSerializer(serializers.ModelSerializer):
    # Las claves son nombres del JSON: son las que ve el cliente en ``campos``.
    FORBIDDEN_FIELD_MESSAGES = {
        "estado": "El estado solo se cambia con POST /api/problems/v1/problemas/{id}/estado/.",
        "origen": "El origen no se puede modificar.",
    }

    class Meta:
        model = Problem
        fields = ("titulo", "descripcion", "prioridad", "causa_raiz", "asignado_a_id")
        extra_kwargs = json_sources(*fields)

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
    estado = serializers.ChoiceField(source="status", choices=Problem.Status.choices)
    causa_raiz = serializers.CharField(source="root_cause", required=False, allow_blank=True)

    def validate(self, attrs):
        current, target = self.instance.status, attrs["status"]
        if not states.is_valid_transition(current, target):
            raise Conflict(
                states.invalid_transition_message(current, target),
                error_code="transicion_invalida",
            )
        root_cause = attrs.get("root_cause", self.instance.root_cause)
        if target in states.ROOT_CAUSE_REQUIRED_STATES and not root_cause.strip():
            raise serializers.ValidationError(
                {"causa_raiz": f"Se requiere la causa raíz para pasar a {target}."}
            )
        return attrs

    def update(self, instance, validated_data):
        target = validated_data["status"]
        updated_fields = ["status", "updated_at"]
        if target == Problem.Status.RESOLVED:
            instance.resolved_at = timezone.now()
            updated_fields.append("resolved_at")
        elif states.is_reopening(instance.status, target):
            instance.resolved_at = None
            updated_fields.append("resolved_at")
        if "root_cause" in validated_data:
            instance.root_cause = validated_data["root_cause"]
            updated_fields.append("root_cause")
        instance.status = target
        instance.save(update_fields=updated_fields)
        return instance


@extend_schema_serializer(component_name="ProblemaIncidente")
class ProblemIncidentReadSerializer(serializers.ModelSerializer):
    """Solo lectura: id, problema_id y vinculado_en los asigna el servicio."""

    problema_id = serializers.IntegerField(source="problem_id", read_only=True)

    class Meta:
        model = ProblemIncident
        fields = ("id", "problema_id", "incidente_id", "vinculado_en")
        read_only_fields = fields
        extra_kwargs = {
            "incidente_id": {"source": "incident_id"},
            "vinculado_en": {"source": "linked_at"},
        }


@extend_schema_serializer(component_name="VincularIncidente")
class IncidentLinkSerializer(serializers.Serializer):
    """El ID se guarda tal cual: no se consulta ni valida contra el servicio de Incidencias."""

    incidente_id = serializers.CharField(source="incident_id", min_length=1, max_length=64)


# --- Errores conocidos (#273) --------------------------------------------------------------------

KNOWN_ERROR_JSON_FIELDS = {
    "titulo": "title",
    "descripcion": "description",
    "causa_raiz": "root_cause",
    "workaround": "workaround",
    "articulo_kb_id": "kb_article_id",
    "activo": "is_active",
}
KNOWN_ERROR_SOURCES = {
    name: {"source": source} for name, source in KNOWN_ERROR_JSON_FIELDS.items() if name != source
}


@extend_schema_serializer(component_name="ErrorConocido")
class KnownErrorReadSerializer(serializers.ModelSerializer):
    """Solo lectura; ``articulo_kb_id`` es texto: no se consulta el servicio de Knowledge."""

    problema_id = serializers.IntegerField(source="problem_id", read_only=True)

    class Meta:
        model = KnownError
        fields = ("id", "problema_id", *KNOWN_ERROR_JSON_FIELDS, "creado_en", "actualizado_en")
        read_only_fields = fields
        extra_kwargs = {
            **KNOWN_ERROR_SOURCES,
            "creado_en": {"source": "created_at"},
            "actualizado_en": {"source": "updated_at"},
        }


@extend_schema_serializer(component_name="ErrorConocidoCrear")
class KnownErrorCreateSerializer(serializers.ModelSerializer):
    # El contrato pide 400 (no 404) si el problema no existe: es un dato inválido del cuerpo.
    problema_id = serializers.PrimaryKeyRelatedField(
        source="problem",
        queryset=Problem.objects.all(),
        error_messages={
            "does_not_exist": "No existe el problema {pk_value}.",
            "incorrect_type": "Debe ser el ID numérico de un problema.",
        },
    )

    class Meta:
        model = KnownError
        fields = ("problema_id", *KNOWN_ERROR_JSON_FIELDS)
        extra_kwargs = KNOWN_ERROR_SOURCES


@extend_schema_serializer(component_name="ErrorConocidoActualizar")
class KnownErrorUpdateSerializer(serializers.ModelSerializer):
    """Los campos de solo lectura (``problema_id``, ``id``, fechas) se ignoran, como en DRF.

    Si el cuerpo no trae ningún campo modificable es un 400 (``minProperties: 1``).
    """

    class Meta:
        model = KnownError
        fields = tuple(KNOWN_ERROR_JSON_FIELDS)
        extra_kwargs = KNOWN_ERROR_SOURCES

    def to_internal_value(self, data):
        if isinstance(data, Mapping) and not any(field in self.fields for field in data):
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: "Envía al menos un campo modificable."}
            )
        return super().to_internal_value(data)
