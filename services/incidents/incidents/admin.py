from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "priority", "status", "assigned_to", "created_at"]
    list_filter = ["status", "priority"]
    search_fields = ["title"]
    readonly_fields = [
        "code",
        "priority",
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
    ]
    fieldsets = [
        (None, {"fields": ["code", "title", "description", "status"]}),
        ("Prioridad (impacto × urgencia)", {"fields": ["impact", "urgency", "priority"]}),
        ("Asignación", {"fields": ["reported_by", "assigned_to", "assignment_group"]}),
        (
            "Relación con otros servicios",
            {"fields": ["affected_service", "source_event_id", "problem_id"]},
        ),
        (
            "Fechas",
            {"fields": ["sla_due_at", "created_at", "updated_at", "resolved_at", "closed_at"]},
        ),
    ]

    @admin.display(description="código", ordering="id")
    def code(self, obj: Incident) -> str:
        return obj.code
