from rest_framework import serializers


def nullable_text(value):
    """La BD guarda "" en los textos opcionales; la API (contrato) devuelve null."""
    return None if value == "" else value


class ErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
    fields = serializers.DictField(child=serializers.CharField(), required=False)


# Campos obligatorios de cada componente según contracts/events/openapi.yaml.
REQUIRED_BY_COMPONENT = {
    "EventCreate": ["origin", "title", "message"],
    "EventRead": [
        "id",
        "origin",
        "event_type",
        "category",
        "title",
        "message",
        "payload",
        "state",
        "action_required",
        "fingerprint",
        "occurrence_count",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
    ],
    "EventListItem": [
        "id",
        "origin",
        "event_type",
        "category",
        "title",
        "state",
        "occurrence_count",
        "last_seen_at",
        "created_at",
    ],
    "EventDetail": [
        "id",
        "origin",
        "event_type",
        "category",
        "title",
        "message",
        "payload",
        "state",
        "action_required",
        "fingerprint",
        "occurrence_count",
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
    ],
    "EventPage": ["count", "results"],
    "Error": ["code", "detail"],
    # Ciclo de vida
    "EventTransition": ["to_state"],
    "AllowedTransitions": ["state", "allowed"],
    "EventHistoryEntry": ["id", "changed_at", "change_type", "actor_type"],
    "EventHistoryPage": ["count", "results"],
}


def contract_required_postprocessing(result, generator, request, public):
    """Hook de drf-spectacular: alinea los `required` generados con los del contrato."""
    schemas = result.get("components", {}).get("schemas", {})
    for name, required in REQUIRED_BY_COMPONENT.items():
        if name in schemas:
            schemas[name]["required"] = required
    return result
