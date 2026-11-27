import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .base import AuditModel
from .catalog import BusinessService, EventSource, SlaPolicy
from .choices import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    ClosureCode,
    EventCategory,
    EventOrigin,
    EventState,
    EventType,
    Impact,
    MatchKind,
    Priority,
    Urgency,
)


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

    impact = models.CharField(max_length=10, choices=Impact.choices, blank=True, default="")

    urgency = models.CharField(max_length=10, choices=Urgency.choices, blank=True, default="")

    priority = models.CharField(max_length=10, choices=Priority.choices, blank=True, default="")

    state = models.CharField(max_length=12, choices=EventState.choices, default=EventState.NEW)

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
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_code = models.CharField(
        max_length=20, choices=ClosureCode.choices, blank=True, default=""
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
            models.Index(fields=["assigned_to_ref", "state"], name="ix_event_assignee_state"),
            models.Index(fields=["-created_at"], name="ix_event_created_desc"),
        ]

    def __str__(self) -> str:
        return f"[{self.state}] {self.title}"

    def can_transition_to(self, new_state: str) -> bool:
        return EventState(new_state) in ALLOWED_TRANSITIONS.get(EventState(self.state), set())


class EventOccurrence(models.Model):
    """Cada llegada de un evento (la primera y las repiticiones). Base de n_eventos_similares"""

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="occurrences")
    occurred_at = models.DateTimeField()
    fingerprint = models.CharField(max_length=64)
    source = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)
    ingestion_key = models.CharField(max_length=100, blank=True, default="")
    received_at = models.DateTimeField(auto_now_add=True)
    match_kind = models.CharField(max_length=8, choices=MatchKind.choices, default=MatchKind.NEW)
    similarity = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "event_occurrence"
        indexes = [
            models.Index(fields=["fingerprint", "-occurred_at"], name="ix_occ_fp_time"),
            models.Index(fields=["event", "-occurred_at"], name="ix_occ_event_time"),
        ]

    def __str__(self) -> str:
        return f"{self.fingerprint[:8]} @ {self.occurred_at:%Y-%m-%d %H:%M} ({self.match_kind})"
