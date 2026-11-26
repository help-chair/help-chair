import uuid

from django.db import models
from django.utils import timezone

from .choices import OutboxStatus


class OutboxMessage(models.Model):
    """Mensaje pendiente de publicar en el broker (patrón *outbox*).

    Se escribe en la **misma transacción** que el cambio que lo origina (events/outbox/messages.py)
    y lo publica después `manage.py publish_outbox`. `id` es el `id` del sobre común
    (contracts/messages/event-envelope.json) y la clave de idempotencia de los consumidores.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aggregate_id = models.UUIDField()  # event.id
    message_type = models.CharField(max_length=80)  # event.state_changed, event.routed...
    version = models.PositiveSmallIntegerField(default=1)
    subject = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()
    correlation_id = models.UUIDField(null=True, blank=True)

    status = models.CharField(
        max_length=10, choices=OutboxStatus.choices, default=OutboxStatus.PENDING
    )
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "outbox_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"], name="ix_outbox_status_next"),
            models.Index(fields=["aggregate_id", "created_at"], name="ix_outbox_aggregate"),
        ]

    def __str__(self) -> str:
        return f"{self.message_type} · {self.status} ({self.id})"
