from django.db import models
from django.db.models import Q

from .base import AuditModel
from .choices import (
    EventCategory,
    EventType,
    Impact,
    Priority,
    RecurrenceAction,
    ServiceImportance,
    SourceKind,
    Urgency,
)


class BusinessService(AuditModel):
    """Servicio de TI del catálogo de la empresa, con su importancia."""

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    importance = models.CharField(max_length=10, choices=ServiceImportance.choices)
    owner_department_ref = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "business_service"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class SlaPolicy(AuditModel):
    """Tiempos objetivo por prioridad. `service` nulo = política por defecto."""

    service = models.ForeignKey(
        BusinessService,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="sla_policies",
    )

    priority = models.CharField(max_length=10, choices=Priority.choices)
    response_minutes = models.PositiveIntegerField()
    resolution_minutes = models.PositiveIntegerField()
    uses_business_hours = models.BooleanField(default=False)

    class Meta:
        db_table = "sla_policy"
        ordering = ["service_id", "priority"]
        constraints = [
            models.UniqueConstraint(fields=["service", "priority"], name="uq_sla_service_priority"),
            models.UniqueConstraint(
                fields=["priority"],
                condition=Q(service__isnull=True),
                name="uq_sla_default_priority",
            ),
        ]

    def __str__(self) -> str:
        return f"SLA {self.priority} · {self.service or 'por defecto'}"


class PriorityMatrix(AuditModel):
    """Prioridad base a partir de impacto x urgencia."""

    impact = models.CharField(max_length=10, choices=Impact.choices)
    urgency = models.CharField(max_length=10, choices=Urgency.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices)

    class Meta:
        db_table = "priority_matrix"
        constraints = [
            models.UniqueConstraint(
                fields=["impact", "urgency"], name="uq_priority_matrix_impact_urgency"
            )
        ]

    def __str__(self) -> str:
        return f"{self.impact} x {self.urgency} -> {self.priority}"


class EventSource(AuditModel):
    """Fuente registrada de eventos (fase 4: ingesta por webhook con clave de API)."""

    name = models.CharField(max_length=100, unique=True)
    kind = models.CharField(max_length=12, choices=SourceKind.choices)
    api_key_hash = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "event_source"

    def __str__(self) -> str:
        return self.name


class RecurrencePolicy(AuditModel):
    """Umbral de recurrencia (N veces en T días) de las reglas 3 y 7.

    Un campo vacío significa "cualquiera". Gana la política activa más específica.
    """

    event_type = models.CharField(max_length=12, choices=EventType.choices)
    category = models.CharField(
        max_length=15, choices=EventCategory.choices, blank=True, default=""
    )

    service = models.ForeignKey(
        BusinessService,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="recurrence_policies",
    )

    threshold_count = models.PositiveIntegerField()
    window_days = models.PositiveIntegerField()
    action = models.CharField(
        max_length=20, choices=RecurrenceAction.choices, default=RecurrenceAction.WATCH_ALERT
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "recurrence_policy"
        constraints = [
            models.CheckConstraint(
                condition=Q(threshold_count__gte=1), name="ck_recurrence_threshold_gte_1"
            ),
            models.CheckConstraint(
                condition=Q(window_days__gte=1), name="ck_recurrence_window_gte_1"
            ),
        ]

    def __str__(self) -> str:
        scope = f"{self.event_type or '*'}/{self.category or '*'}"
        return f"{scope}: {self.threshold_count} en {self.window_days} d"
