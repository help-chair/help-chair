from django.contrib import admin
from django.utils import timezone

from .models import (
    BusinessService,
    Event,
    EventHistory,
    EventSource,
    OutboxMessage,
    OutboxStatus,
    PriorityMatrix,
    PriorityModifier,
    RecurrencePolicy,
    SlaPolicy,
)


@admin.register(BusinessService)
class BusinessServiceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "importance", "owner_department_ref", "is_active")
    list_filter = ("importance", "is_active")
    search_fields = ("code", "name")


@admin.register(SlaPolicy)
class SlaPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "service",
        "priority",
        "response_minutes",
        "resolution_minutes",
        "uses_business_hours",
    )
    list_filter = ("priority", "uses_business_hours")
    list_select_related = ("service",)


@admin.register(PriorityMatrix)
class PriorityMatrixAdmin(admin.ModelAdmin):
    list_display = ("impact", "urgency", "priority")
    list_filter = ("impact", "urgency", "priority")


@admin.register(PriorityModifier)
class PriorityModifierAdmin(admin.ModelAdmin):
    list_display = ("code", "condition_field", "condition_value", "levels_delta", "is_active")
    list_filter = ("condition_field", "is_active")
    search_fields = ("code",)


@admin.register(EventSource)
class EventSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name",)
    exclude = ("api_key_hash",)


@admin.register(RecurrencePolicy)
class RecurrencePolicyAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "event_type",
        "category",
        "service",
        "threshold_count",
        "window_days",
        "action",
        "is_active",
    )
    list_filter = ("action", "is_active", "event_type", "category", "service")
    search_fields = ("service__code", "service__name")
    list_select_related = ("service",)
    list_editable = ("is_active", "action")


class EventHistoryInline(admin.TabularInline):
    """Bitácora dentro del evento: solo lectura (es de solo inserción)."""

    model = EventHistory
    extra = 0
    can_delete = False
    fields = (
        "changed_at",
        "change_type",
        "actor_type",
        "actor_ref",
        "from_state",
        "to_state",
        "rule_code",
        "description",
    )
    readonly_fields = fields
    ordering = ("-changed_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "event_type",
        "state",
        "priority",
        "service",
        "occurrence_count",
        "created_at",
    )
    list_filter = ("state", "event_type", "category", "priority", "origin")
    search_fields = ("title", "message", "fingerprint")
    list_select_related = ("service",)
    date_hierarchy = "created_at"
    readonly_fields = ("id", "fingerprint", "created_at", "updated_at")
    inlines = [EventHistoryInline]


@admin.register(EventHistory)
class EventHistoryAdmin(admin.ModelAdmin):
    """La bitácora no se edita ni se borra desde el admin."""

    list_display = ("event", "changed_at", "change_type", "actor_type", "to_state")
    list_filter = ("change_type", "actor_type")
    search_fields = ("event__id", "event__title", "description")
    list_select_related = ("event",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OutboxMessage)
class OutboxMessageAdmin(admin.ModelAdmin):
    """Mensajes de salida al broker. Solo lectura, salvo la acción de reintentar."""

    list_display = ("created_at", "message_type", "subject", "status", "attempts", "published_at")
    list_filter = ("status", "message_type")
    search_fields = ("id", "aggregate_id", "subject", "last_error")
    date_hierarchy = "created_at"
    actions = ["retry_messages"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description="Reintentar (volver a PENDING)")
    def retry_messages(self, request, queryset):
        updated = queryset.exclude(status=OutboxStatus.PUBLISHED).update(
            status=OutboxStatus.PENDING, attempts=0, next_attempt_at=timezone.now()
        )
        self.message_user(request, f"{updated} mensaje(s) vuelven a PENDING.")
