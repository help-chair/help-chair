import uuid

from django.db import models


class CatalogItem(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "nuevo", "Nuevo"
        ASSIGNED = "asignado", "Asignado"
        IN_PROGRESS = "en_proceso", "En proceso"
        RESOLVED = "resuelto", "Resuelto"
        CLOSED = "cerrado", "Cerrado"
        REOPENED = "reabierto", "Reabierto"
        CANCELLED = "cancelado", "Cancelado"

    class RequestType(models.TextChoices):
        SERVICE = "servicio", "Servicio"
        CHANGE = "cambio", "Cambio"

    class ApprovalStatus(models.TextChoices):
        NOT_REQUIRED = "no_requerida", "No requerida"
        PENDING = "pendiente", "Pendiente de aprobación"
        APPROVED = "aprobado", "Aprobado"
        REJECTED = "rechazado", "Rechazado"

    TRANSITIONS = {
        Status.NEW: {Status.ASSIGNED, Status.CANCELLED},
        Status.ASSIGNED: {Status.IN_PROGRESS, Status.CANCELLED},
        Status.IN_PROGRESS: {Status.RESOLVED, Status.CANCELLED},
        Status.RESOLVED: {Status.CLOSED, Status.REOPENED},
        Status.REOPENED: {Status.ASSIGNED, Status.IN_PROGRESS},
        Status.CLOSED: set(),
        Status.CANCELLED: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_type = models.CharField(
        max_length=20, choices=RequestType.choices, default=RequestType.SERVICE
    )
    service = models.ForeignKey(
        CatalogItem, on_delete=models.PROTECT, related_name="requests"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_REQUIRED,
    )
    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)

    requester_id = models.BigIntegerField()
    assignee_id = models.BigIntegerField(null=True, blank=True)
    event_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    cancellation_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "assignee_id"]),
            models.Index(fields=["request_type", "approval_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event_id"],
                condition=~models.Q(event_id=""),
                name="unique_non_empty_event_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"

    @property
    def requires_approval(self) -> bool:
        return self.request_type == self.RequestType.CHANGE

    def can_transition_to(self, next_status: str) -> bool:
        if next_status not in self.TRANSITIONS[self.status]:
            return False
        if (
            self.requires_approval
            and next_status in {self.Status.IN_PROGRESS, self.Status.RESOLVED}
            and self.approval_status != self.ApprovalStatus.APPROVED
        ):
            return False
        return True