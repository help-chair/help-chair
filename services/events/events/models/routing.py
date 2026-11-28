from django.db import models

from .choices import Destination, RoutingStatus
from .event import Event


class EventRouting(models.Model):
    """Resultado de entregar un evento a un servicio destino (uno por evento y destino)."""

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="routings")
    destination = models.CharField(max_length=15, choices=Destination.choices)
    rule_code = models.CharField(max_length=20)
    status = models.CharField(
        max_length=10, choices=RoutingStatus.choices, default=RoutingStatus.PENDING
    )

    remote_id = models.CharField(max_length=64, blank=True, default="")
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_routing"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "destination"], name="uq_routing_event_destination"
            )
        ]
        indexes = [models.Index(fields=["status", "last_attempt_at"], name="ix_routing_status")]

    def __str__(self) -> str:
        return f"{self.event_id} -> {self.destination} [{self.status}]"
