from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .base import AuditModel
from .choices import (
    EventCategory,
    EventType,
    Impact,
    ModifierField,
    Priority,
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


class PriorityModifier(AuditModel):
    code = models.SlugField(max_length=50, unique=True)
    condition_field = models.CharField(max_length=20, choices=ModifierField.choices)
    condition_value = models.CharField(max_length=50)
    levels_delta = models.SmallIntegerField(
        validators=[MinValueValidator(-3), MaxValueValidator(3)]
    )
    is_active = models.BooleanField(default=True)

    VALID_VALUES = {
        ModifierField.SERVICE_IMPORTANCE: ServiceImportance.values,
        ModifierField.EVENT_CATEGORY: EventCategory.values,
        ModifierField.EVENT_TYPE: EventType.values,
    }

    class Meta:
        db_table = "priority_modifier"
        ordering = ["code"]

    def __str__(self) -> str:
        condition = f"{self.condition_field}={self.condition_value}"
        return f"{self.code} · {condition} ({self.levels_delta:+d})"

    def clean(self):
        super().clean()
        if self.levels_delta == 0:
            raise ValidationError({"levels_delta": "No puede ser cero."})
        if self.condition_field == ModifierField.OCCURRENCE_COUNT:
            if not self.condition_value.isdigit() or int(self.condition_value) < 1:
                raise ValidationError({"condition_value": "Debe ser un entero mayor que cero."})
            return
        valid_values = self.VALID_VALUES.get(self.condition_field, [])
        if self.condition_value not in valid_values:
            raise ValidationError(
                {"condition_value": f"Valores válidos: {', '.join(valid_values)}."}
            )


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
