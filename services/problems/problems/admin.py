"""Admin de Django; columnas y formularios usan los ``verbose_name`` en español."""

from django.contrib import admin

from .models import KnownError, Problem, ProblemIncident


class ProblemIncidentInline(admin.TabularInline):
    model = ProblemIncident
    extra = 0
    readonly_fields = ["linked_at"]


class KnownErrorInline(admin.StackedInline):
    model = KnownError
    extra = 0


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "status", "priority", "origin", "assignee_id", "created_at"]
    list_filter = ["status", "priority", "origin"]
    search_fields = ["title", "description", "root_cause"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProblemIncidentInline, KnownErrorInline]


@admin.register(KnownError)
class KnownErrorAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "problem", "is_active", "kb_article_id", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title", "description", "root_cause", "workaround"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProblemIncident)
class ProblemIncidentAdmin(admin.ModelAdmin):
    list_display = ["id", "problem", "incident_id", "linked_at"]
    search_fields = ["incident_id"]
