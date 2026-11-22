"""Modelo de incidente (issue #119).

Los datos que pertenecen a otros servicios (usuarios de Accesos, servicios y eventos
de Eventos, problemas de Problemas) se guardan como su ID en texto, nunca como llave
foránea: cada servicio tiene su propia base de datos.
"""

from django.db import models
from django.utils import timezone

from .priority import Impact, Priority, Urgency, calculate_priority


class Status(models.TextChoices):
    """Estados del ciclo de vida (docs/ARCHITECTURE.md §6)."""

    NEW = "nuevo", "Nuevo"
    ASSIGNED = "asignado", "Asignado"
    IN_PROGRESS = "en_proceso", "En proceso"
    ON_HOLD = "en_espera", "En espera"
    RESOLVED = "resuelto", "Resuelto"
    CLOSED = "cerrado", "Cerrado"
    REJECTED = "rechazado", "Rechazado"
    CANCELLED = "cancelado", "Cancelado"
    REOPENED = "reabierto", "Reabierto"


# Transiciones permitidas: estado actual -> estados a los que puede pasar.
# Cerrado, Rechazado y Cancelado son finales.
TRANSITIONS: dict[str, frozenset[str]] = {
    Status.NEW: frozenset({Status.ASSIGNED, Status.REJECTED, Status.CANCELLED}),
    Status.ASSIGNED: frozenset(
        {Status.IN_PROGRESS, Status.ON_HOLD, Status.REJECTED, Status.CANCELLED}
    ),
    Status.IN_PROGRESS: frozenset({Status.ON_HOLD, Status.RESOLVED, Status.CANCELLED}),
    Status.ON_HOLD: frozenset({Status.IN_PROGRESS, Status.CANCELLED}),
    Status.RESOLVED: frozenset({Status.CLOSED, Status.REOPENED}),
    Status.REOPENED: frozenset({Status.ASSIGNED, Status.IN_PROGRESS}),
    Status.CLOSED: frozenset(),
    Status.REJECTED: frozenset(),
    Status.CANCELLED: frozenset(),
}


class Incident(models.Model):
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True, default="")

    impact = models.CharField("impacto", max_length=10, choices=Impact.choices)
    urgency = models.CharField("urgencia", max_length=10, choices=Urgency.choices)
    priority = models.CharField(
        "prioridad",
        max_length=2,
        choices=Priority.choices,
        editable=False,
        help_text="Se calcula sola con la matriz impacto × urgencia.",
    )
    status = models.CharField("estado", max_length=12, choices=Status.choices, default=Status.NEW)

    # IDs de otros servicios (texto, sin llave foránea)
    affected_service = models.CharField(
        "servicio afectado",
        max_length=100,
        blank=True,
        default="",
        help_text="ID del servicio del catálogo (Eventos).",
    )
    reported_by = models.CharField(
        "reportado por", max_length=64, help_text="ID del usuario que reporta (Accesos)."
    )
    assigned_to = models.CharField(
        "asignado a",
        max_length=64,
        blank=True,
        default="",
        help_text="ID del agente asignado (Accesos). Vacío = sin asignar.",
    )
    assignment_group = models.CharField(
        "grupo",
        max_length=100,
        blank=True,
        default="",
        help_text="Grupo o departamento resolutor (Accesos).",
    )
    source_event_id = models.CharField(
        "evento de origen",
        max_length=64,
        blank=True,
        default="",
        help_text="ID del evento que originó el incidente (Eventos).",
    )
    problem_id = models.CharField(
        "problema relacionado",
        max_length=64,
        blank=True,
        default="",
        help_text="ID del problema asociado (Problemas).",
    )

    sla_due_at = models.DateTimeField(
        "vence SLA",
        null=True,
        blank=True,
        help_text="Fecha objetivo de resolución. Se calculará con el SLA de Eventos (Fase 2).",
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)
    resolved_at = models.DateTimeField("resuelto", null=True, blank=True)
    closed_at = models.DateTimeField("cerrado", null=True, blank=True)

    class Meta:
        verbose_name = "incidente"
        verbose_name_plural = "incidentes"
        ordering = ["priority", "-created_at"]
        indexes = [models.Index(fields=["status", "priority"])]

    def __str__(self) -> str:
        return f"{self.code} {self.title}"

    def save(self, *args, **kwargs):
        # La prioridad nunca se asigna a mano: siempre sale de la matriz.
        self.priority = calculate_priority(self.impact, self.urgency)
        # Marcas de tiempo del ciclo de vida
        if self.status == Status.RESOLVED and self.resolved_at is None:
            self.resolved_at = timezone.now()
        elif self.status == Status.REOPENED:
            self.resolved_at = None
        if self.status == Status.CLOSED and self.closed_at is None:
            self.closed_at = timezone.now()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = {*update_fields, "priority", "resolved_at", "closed_at"}
        super().save(*args, **kwargs)

    @property
    def code(self) -> str:
        """Identificador legible, p. ej. INC-000042."""
        return f"INC-{self.pk:06d}" if self.pk else "INC-nuevo"

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in TRANSITIONS[self.status]
