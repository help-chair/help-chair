"""Serializers del ciclo de vida: transiciones, historial y PATCH de gestión."""

from rest_framework import serializers

from ..models import (
    ActorType,
    ChangeType,
    ClosureCode,
    EventCategory,
    EventHistory,
    EventState,
    Impact,
    Urgency,
)
from .common import nullable_text


class EventTransitionSerializer(serializers.Serializer):
    to_state = serializers.ChoiceField(choices=EventState.choices)
    reason = serializers.CharField(required=False, allow_blank=True)
    closure_code = serializers.ChoiceField(choices=ClosureCode.choices, required=False)


class AllowedTransitionsSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=EventState.choices)
    allowed = serializers.ListField(child=serializers.ChoiceField(choices=EventState.choices))


class EventUpdateSerializer(serializers.Serializer):
    """PATCH /events/{id}: solo campos de gestión. Todos opcionales, pero al menos uno."""

    assigned_to_ref = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=64
    )
    assigned_group_ref = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=64
    )
    impact = serializers.ChoiceField(choices=Impact.choices, required=False)
    urgency = serializers.ChoiceField(choices=Urgency.choices, required=False)
    category = serializers.ChoiceField(choices=EventCategory.choices, required=False)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Envía al menos un campo.")
        return attrs


class EventHistoryEntrySerializer(serializers.ModelSerializer):
    actor_ref = serializers.CharField(read_only=True, allow_null=True, required=False)
    from_state = serializers.ChoiceField(
        choices=EventState.choices, read_only=True, allow_null=True, required=False
    )
    to_state = serializers.ChoiceField(
        choices=EventState.choices, read_only=True, allow_null=True, required=False
    )
    field_name = serializers.CharField(read_only=True, allow_null=True, required=False)
    description = serializers.CharField(read_only=True, allow_null=True, required=False)
    rule_code = serializers.CharField(read_only=True, allow_null=True, required=False)
    change_type = serializers.ChoiceField(choices=ChangeType.choices, read_only=True)
    actor_type = serializers.ChoiceField(choices=ActorType.choices, read_only=True)

    class Meta:
        model = EventHistory
        fields = [
            "id",
            "changed_at",
            "change_type",
            "actor_type",
            "actor_ref",
            "from_state",
            "to_state",
            "field_name",
            "old_value",
            "new_value",
            "description",
            "rule_code",
            "metadata",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for name in (
            "actor_ref",
            "from_state",
            "to_state",
            "field_name",
            "description",
            "rule_code",
        ):
            data[name] = nullable_text(getattr(instance, name))
        return data


class EventHistoryPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True, required=False)
    previous = serializers.URLField(allow_null=True, required=False)
    results = EventHistoryEntrySerializer(many=True)
