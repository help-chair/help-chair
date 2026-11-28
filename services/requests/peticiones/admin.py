from django.contrib import admin

from .models import CatalogItem, SatisfactionSurvey, ServiceRequest


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "request_type",
        "service",
        "status",
        "approval_status",
        "requester_id",
        "assignee_id",
        "created_at",
    ]
    list_filter = ["status", "request_type", "approval_status", "service"]
    search_fields = ["title", "description", "event_id"]


@admin.register(SatisfactionSurvey)
class SatisfactionSurveyAdmin(admin.ModelAdmin):
    list_display = ["service_request", "rating", "respondent_id", "answered_at"]
    list_filter = ["rating"]
