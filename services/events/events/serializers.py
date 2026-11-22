from rest_framework import serializers

from .models import (
    BusinessService,
    Event,
    EventCategory,
    EventOrigin,
    EventSource,
    EventType,
    Impact,
    Priority,
    Urgency,
)
from .models.choices import ClosureCode, Destination


def nullable_text(value):
    return None if value == "" else value


class ErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
    fields = serializers.DictField(child=serializers.CharField(), required=False)


def contract_required_postprocessing(result, generator, request, public):
    required_by_component = {
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
    }
    schemas = result.get("components", {}).get("schemas", {})
    for name, required in required_by_component.items():
        if name in schemas:
            schemas[name]["required"] = required
    return result


class BusinessServiceSerializer(serializers.ModelSerializer):
    description = serializers.CharField(
        read_only=True, allow_null=True, allow_blank=True, required=False
    )
    owner_department_ref = serializers.CharField(
        read_only=True, allow_null=True, allow_blank=True, required=False
    )

    class Meta:
        model = BusinessService
        fields = [
            "id",
            "code",
            "name",
            "description",
            "importance",
            "owner_department_ref",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["description"] = nullable_text(instance.description)
        data["owner_department_ref"] = nullable_text(instance.owner_department_ref)
        return data


class EventCreateSerializer(serializers.Serializer):
    origin = serializers.ChoiceField(choices=EventOrigin.choices, required=True)
    title = serializers.CharField(min_length=1, max_length=200)
    message = serializers.CharField(min_length=1)
    event_type = serializers.ChoiceField(choices=EventType.choices, required=False)
    category = serializers.ChoiceField(choices=EventCategory.choices, required=False)
    service_code = serializers.SlugRelatedField(
        slug_field="code",
        queryset=BusinessService.objects.filter(is_active=True),
        source="service",
        required=False,
        allow_null=True,
    )
    source_name = serializers.SlugRelatedField(
        slug_field="name",
        queryset=EventSource.objects.filter(is_active=True),
        source="source",
        required=False,
        allow_null=True,
    )
    impact = serializers.ChoiceField(choices=Impact.choices, required=False)
    urgency = serializers.ChoiceField(choices=Urgency.choices, required=False)
    action_required = serializers.BooleanField(default=True)
    payload = serializers.DictField(default=dict)
    occurred_at = serializers.DateTimeField(required=False)
    ingestion_key = serializers.CharField(max_length=100, required=False)


class EventReadSerializer(serializers.ModelSerializer):
    service_code = serializers.CharField(read_only=True, allow_null=True, required=False)
    source_name = serializers.CharField(read_only=True, allow_null=True, required=False)
    payload = serializers.DictField(read_only=True)
    impact = serializers.ChoiceField(
        choices=Impact.choices, read_only=True, allow_null=True, required=False
    )
    urgency = serializers.ChoiceField(
        choices=Urgency.choices, read_only=True, allow_null=True, required=False
    )
    priority = serializers.ChoiceField(
        choices=Priority.choices, read_only=True, allow_null=True, required=False
    )
    reporter_ref = serializers.CharField(read_only=True, allow_null=True, required=False)
    assigned_to_ref = serializers.CharField(read_only=True, allow_null=True, required=False)
    assigned_group_ref = serializers.CharField(
        read_only=True, allow_null=True, required=False
    )
    sla_policy_id = serializers.IntegerField(
        read_only=True, allow_null=True, required=False
    )
    response_due_at = serializers.DateTimeField(read_only=True, allow_null=True, required=False)
    resolution_due_at = serializers.DateTimeField(
        read_only=True, allow_null=True, required=False
    )
    resolved_at = serializers.DateTimeField(read_only=True, allow_null=True, required=False)
    closed_at = serializers.DateTimeField(read_only=True, allow_null=True, required=False)
    closure_code = serializers.ChoiceField(
        choices=ClosureCode.choices, read_only=True, allow_null=True, required=False
    )
    state_reason = serializers.CharField(read_only=True, allow_null=True, required=False)
    fingerprint = serializers.CharField(
        min_length=64, max_length=64, read_only=True
    )
    occurrence_count = serializers.IntegerField(
        min_value=1, read_only=True
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "origin",
            "event_type",
            "category",
            "title",
            "message",
            "payload",
            "service_code",
            "source_name",
            "impact",
            "urgency",
            "priority",
            "state",
            "action_required",
            "fingerprint",
            "occurrence_count",
            "first_seen_at",
            "last_seen_at",
            "reporter_ref",
            "assigned_to_ref",
            "assigned_group_ref",
            "sla_policy_id",
            "response_due_at",
            "resolution_due_at",
            "resolved_at",
            "closed_at",
            "closure_code",
            "state_reason",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["service_code"] = instance.service.code if instance.service else None
        data["source_name"] = instance.source.name if instance.source else None
        payload = dict(instance.payload or {})
        payload.pop("_ingestion_key", None)
        data["payload"] = payload
        data["impact"] = nullable_text(instance.impact)
        data["urgency"] = nullable_text(instance.urgency)
        data["priority"] = nullable_text(instance.priority)
        data["reporter_ref"] = nullable_text(instance.reporter_ref)
        data["assigned_to_ref"] = nullable_text(instance.assigned_to_ref)
        data["assigned_group_ref"] = nullable_text(instance.assigned_group_ref)
        data["closure_code"] = nullable_text(instance.closure_code)
        data["state_reason"] = nullable_text(instance.state_reason)
        return data


class EventListItemSerializer(serializers.ModelSerializer):
    service_code = serializers.CharField(read_only=True, allow_null=True, required=False)
    destination = serializers.ChoiceField(
        choices=[*Destination.values, None],
        read_only=True,
        allow_null=True,
        required=False,
    )
    assigned_to_ref = serializers.CharField(read_only=True, allow_null=True, required=False)
    priority = serializers.ChoiceField(
        choices=Priority.choices, read_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "origin",
            "event_type",
            "category",
            "title",
            "priority",
            "state",
            "service_code",
            "destination",
            "assigned_to_ref",
            "occurrence_count",
            "last_seen_at",
            "resolution_due_at",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["service_code"] = instance.service.code if instance.service else None
        data["destination"] = None
        data["assigned_to_ref"] = nullable_text(instance.assigned_to_ref)
        data["priority"] = nullable_text(instance.priority)
        return data


class EventPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True, required=False)
    previous = serializers.URLField(allow_null=True, required=False)
    results = EventListItemSerializer(many=True)


class EventDetailSerializer(EventReadSerializer):
    service = BusinessServiceSerializer(required=False)
    routing = serializers.ListField(child=serializers.DictField(), read_only=True, required=False)

    class Meta(EventReadSerializer.Meta):
        fields = [*EventReadSerializer.Meta.fields, "service", "routing"]

    def get_routing(self, obj):
        return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["routing"] = []
        if instance.service is None:
            data.pop("service", None)
        return data
