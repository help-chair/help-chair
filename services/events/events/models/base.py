from django.db import models


class AuditModel(models.Model):
    """Huella de auditoría. Los *_ref guardan el `sub` del JWT (Accesos) o "system"."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_ref = models.CharField(max_length=64, blank=True, default="")
    updated_by_ref = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        abstract = True
