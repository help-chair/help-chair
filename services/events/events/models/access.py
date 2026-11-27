from django.db import models
from django.utils import timezone


class ProcessedAccessMessage(models.Model):
    """Inbox idempotente y registro de intentos fallidos recibidos de Accesos."""

    id = models.UUIDField(primary_key=True, editable=False)
    message_type = models.CharField(max_length=80)
    login_group_key = models.CharField(max_length=64, blank=True, default="")
    occurred_at = models.DateTimeField()
    processed_at = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(
        "events.Event",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processed_access_messages",
    )

    class Meta:
        db_table = "processed_access_message"
        indexes = [
            models.Index(
                fields=["message_type", "login_group_key", "occurred_at"],
                name="ix_access_msg_group_time",
            )
        ]

    def __str__(self):
        return f"{self.message_type} · {self.id}"


class AccessLoginFailureGroup(models.Model):
    """Fila de bloqueo por grupo (hash de identificador e IP) al contar fallos concurrentes."""

    key = models.CharField(max_length=64, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.key[:12]
