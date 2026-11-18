from django.contrib import admin

from .models import (
    BusinessService,
    Event,
    EventHistory,
    EventSource,
    PriorityMatrix,
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

@admin.register(EventSource)
class EventSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name",)
    exclude = ("api_key_hash",)

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