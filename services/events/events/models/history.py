from django.db import models
from django.utils import timezone

from .choices import ActorType, ChangeType, EventState
from .event import Event


class EventHistory(models.Model):
    """Bitácora de cambios, solo de inserción."""

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="history")
    changed_at = models.DateTimeField(default=timezone.now)
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    actor_type = models.CharField(max_length=10, choices=ActorType.choices)
    actor_ref = models.CharField(max_length=64, blank=True, default="")
    from_state = models.CharField(max_length=12, choices=EventState.choices, blank=True, default="")
    to_state = models.CharField(max_length=12, choices=EventState.choices, blank=True, default="")
    field_name = models.CharField(max_length=60, blank=True, default="")
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    rule_code = models.CharField(max_length=20, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "event_history"
        indexes = [models.Index(fields=["event", "-changed_at"], name="ix_history_event_changed")]

    def __str__(self) -> str:
        return f"{self.event_id} · {self.change_type} · {self.changed_at:%Y-%m-%d %H:%M}"
