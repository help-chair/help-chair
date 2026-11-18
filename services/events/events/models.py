import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

class AuditModel(models.Model):
    """Huella de auditoría. Los *_ref guardan el `sub` del JWT (Accesos) o "system"."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_ref = models.CharField(max_length=64, blank=True, default="")
    updated_by_ref = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        abstract = True

class EventOrigin(models.TextChoices):
    USER = "USER", "Usuario"
    SYSTEM = "SYSTEM", "Sistema"

class EventType(models.TextChoices):
    INFORMATION = "INFORMATION", "Información"
    WARNING = "WARNING", "Advertencia"
    EXCEPTION = "EXCEPTION", "Excepción"

class EventCategory(models.TextChoices):
    SECURITY = "SECURITY", "Seguridad"
    REQUEST = "REQUEST", "Petición"
    GENERAL = "GENERAL", "General"

class EventState(models.TextChoices):
    NEW = "NEW", "Nuevo"
    ASSIGNED = "ASSIGNED", "Asignado"
    IN_PROGRESS = "IN_PROGRESS", "En proceso"
    ON_HOLD = "ON_HOLD", "En espera"
    RESOLVED = "RESOLVED", "Resuelto"
    CLOSED = "CLOSED", "Cerrado"
    REJECTED = "REJECTED", "Rechazado"
    CANCELLED = "CANCELLED", "Cancelado"
    REOPENED = "REOPENED", "Reabierto"

TERMINAL_STATES = [EventState.CLOSED, EventState.REJECTED, EventState.CANCELLED]

ALLOWED_TRANSITIONS = {
    EventState.NEW: {EventState.ASSIGNED, EventState.REJECTED, EventState.CLOSED},
    EventState.ASSIGNED: {EventState.IN_PROGRESS, EventState.CANCELLED},
    EventState.IN_PROGRESS: {EventState.ON_HOLD, EventState.RESOLVED},
    EventState.ON_HOLD: {EventState.IN_PROGRESS},
    EventState.RESOLVED: {EventState.CLOSED},
    EventState.CLOSED: {EventState.REOPENED},
    EventState.REOPENED: {EventState.ASSIGNED},
    EventState.REJECTED: set(),
    EventState.CANCELLED: set(),
}

class ServiceImportance(models.TextChoices):
    CRITICAL = "CRITICAL", "Crítica"
    HIGH = "HIGH", "Alta"
    MEDIUM = "MEDIUM", "Media"
    LOW = "LOW", "Baja"

class Priority(models.TextChoices):
    CRITICAL = "P1", "Crítica"
    HIGH = "P2", "Alta"
    MEDIUM = "P3", "Media"
    LOW = "P4", "Baja"

class Impact(models.TextChoices):
    HIGH = "HIGH", "Alto"
    MEDIUM = "MEDIUM", "Medio"
    LOW = "LOW", "Bajo"

class Urgency(models.TextChoices):
    HIGH = "HIGH", "Alta"
    MEDIUM = "MEDIUM", "Media"
    LOW = "LOW", "Baja"

class ClosureCode(models.TextChoices):
    AUTO_LOGGED = "AUTO_LOGGED", "Registrado automáticamente"
    KB_RESOLVED = "KB_RESOLVED", "Resuelto por la KB"
    SOLVED = "SOLVED", "Resuelto"
    NOT_APPLICABLE = "NOT_APPLICABLE", "No aplica"

class SourceKind(models.TextChoices):
    SERVICE = "SERVICE", "Servicio"
    WEBHOOK = "WEBHOOK", "Webhook"
    USER_FORM = "USER_FORM", "Formulario de usuario"
    INTERNAL = "INTERNAL", "Interno"

class ChangeType(models.TextChoices):
    STATE_CHANGE = "STATE_CHANGE", "Cambio de estado"
    ASSIGNMENT = "ASSIGNMENT", "Asignación"
    PRIORITY_CHANGE = "PRIORITY_CHANGE", "Cambio de prioridad"
    CLASSIFICATION = "CLASSIFICATION", "Clasificación"
    ROUTING = "ROUTING", "Enrutamiento"
    NOTE = "NOTE", "Nota"
    SYSTEM = "SYSTEM", "Sistema"

class ActorType(models.TextChoices):
    USER = "USER", "Usuario"
    SYSTEM = "SYSTEM", "Sistema"
    RULE = "RULE", "Regla"

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
    uses_business_hours = models.BooleanField(
        default=False
    )

    class Meta:
        db_table = "sla_policy"
        ordering = ["service_id", "priority"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "priority"], name="uq_sla_service_priority"
            ),
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

class Event(AuditModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origin = models.CharField(max_length=10, choices=EventOrigin.choices)
    event_type = models.CharField(max_length=12, choices=EventType.choices)
    category = models.CharField(
        max_length=15, choices=EventCategory.choices, default=EventCategory.GENERAL
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)

    service = models.ForeignKey(
        BusinessService,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
    )
    source = models.ForeignKey(
        EventSource,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
    )

    impact = models.CharField(
        max_length=10, choices=Impact.choices, null=True, blank=True
    )
    urgency = models.CharField(
        max_length=10, choices=Urgency.choices, null=True, blank=True
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, null=True, blank=True
    )

    state = models.CharField(
        max_length=12, choices=EventState.choices, default=EventState.NEW
    )
    action_required = models.BooleanField(default=True)

    fingerprint = models.CharField(max_length=64)
    occurrence_count = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)

    reporter_ref = models.CharField(max_length=64, blank=True, default="")
    assigned_to_ref = models.CharField(max_length=64, blank=True, default="")
    assigned_group_ref = models.CharField(max_length=64, blank=True, default="")

    sla_policy = models.ForeignKey(
        SlaPolicy,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
    )
    response_due_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(
        null=True, blank=True
    )
    closure_code = models.CharField(
        max_length=20, choices=ClosureCode.choices, null=True, blank=True
    )
    state_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "event"
        constraints = [
            models.UniqueConstraint(
                fields=["fingerprint"],
                condition=~Q(state__in=TERMINAL_STATES),
                name="uq_event_open_fingerprint",
            )
        ]
        indexes = [
            models.Index(fields=["state"], name="ix_event_state"),
            models.Index(fields=["state", "priority"], name="ix_event_state_priority"),
            models.Index(fields=["service", "state"], name="ix_event_service_state"),
            models.Index(
                fields=["assigned_to_ref", "state"], name="ix_event_assignee_state"
            ),
            models.Index(fields=["-created_at"], name="ix_event_created_desc"),
        ]

    def __str__(self) -> str:
        return f"[{self.state}] {self.title}"

    def can_transition_to(self, new_state: str) -> bool:
        return EventState(new_state) in ALLOWED_TRANSITIONS.get(
            EventState(self.state), set()
        )


class EventHistory(models.Model):
    """Bitácora de cambios, solo de inserción."""

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="history")
    changed_at = models.DateTimeField(default=timezone.now)
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    actor_type = models.CharField(max_length=10, choices=ActorType.choices)
    actor_ref = models.CharField(max_length=64, blank=True, default="")
    from_state = models.CharField(
        max_length=12, choices=EventState.choices, blank=True, default=""
    )
    to_state = models.CharField(
        max_length=12, choices=EventState.choices, blank=True, default=""
    )
    field_name = models.CharField(max_length=60, blank=True, default="")
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    rule_code = models.CharField(max_length=20, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "event_history"
        indexes = [
            models.Index(
                fields=["event", "-changed_at"], name="ix_history_event_changed"
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.event_id} · {self.change_type} · {self.changed_at:%Y-%m-%d %H:%M}"
        )