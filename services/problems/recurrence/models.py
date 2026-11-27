"""Proyección local de altas observadas; no representa problemas ni sus vínculos."""

from django.db import models


class IncidentObservation(models.Model):
    company_ref = models.CharField(max_length=64)
    incident_ref = models.CharField(max_length=19)
    affected_service = models.CharField(max_length=100)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField()
    payload_digest = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company_ref", "incident_ref"], name="recurrence_incident_unique"
            ),
        ]
        indexes = [
            models.Index(fields=["company_ref", "occurred_at"], name="recurrence_window_idx")
        ]

    def __str__(self):
        return f"Observation {self.pk}"


class ProcessedObservation(models.Model):
    company_ref = models.CharField(max_length=64)
    producer = models.CharField(max_length=32)
    message_id = models.UUIDField()
    message_digest = models.CharField(max_length=64)
    received_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company_ref", "producer", "message_id"], name="recurrence_message_unique"
            ),
        ]

    def __str__(self):
        return f"Processed observation {self.pk}"
