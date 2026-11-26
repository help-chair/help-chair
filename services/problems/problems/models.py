"""Modelos de Gestión de Problemas (ITIL v4): problemas, incidentes vinculados y errores conocidos.

Los IDs de otros servicios (Accesos, Incidencias, Knowledge) se guardan como texto, sin llaves
foráneas: cada servicio tiene su propia base de datos (database per service).

Los identificadores van en inglés; los ``verbose_name`` y las etiquetas de las opciones quedan en
español porque los ve el usuario del admin. Los nombres del JSON del contrato (``titulo``,
``causa_raiz``…) los mapean los serializers.
"""

from django.db import models


class Problem(models.Model):
    """Causa subyacente de uno o más incidentes."""

    # Los valores son los del contrato (EstadoProblema, Prioridad, Origen): no cambiarlos.
    class Status(models.TextChoices):
        REGISTERED = "registrado", "Registrado"
        IN_ANALYSIS = "en_analisis", "En análisis"
        ROOT_CAUSE_IDENTIFIED = "causa_identificada", "Causa identificada"
        KNOWN_ERROR = "error_conocido", "Error conocido"
        RESOLVED = "resuelto", "Resuelto"
        CLOSED = "cerrado", "Cerrado"

    class Priority(models.TextChoices):
        LOW = "baja", "Baja"
        MEDIUM = "media", "Media"
        HIGH = "alta", "Alta"
        CRITICAL = "critica", "Crítica"

    class Origin(models.TextChoices):
        MANUAL = "manual", "Manual"
        PATTERN = "patron", "Patrón detectado"

    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción")
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.REGISTERED
    )
    priority = models.CharField(
        "prioridad", max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    # manual: lo registró una persona; patron: se detectó por incidentes repetidos.
    origin = models.CharField(
        "origen", max_length=10, choices=Origin.choices, default=Origin.MANUAL
    )
    root_cause = models.TextField("causa raíz", blank=True)
    # ID del usuario en el servicio de Accesos (sin llave foránea entre servicios).
    assignee_id = models.CharField("asignado a (ID de usuario)", max_length=64, blank=True)
    created_at = models.DateTimeField("creado en", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado en", auto_now=True)
    resolved_at = models.DateTimeField("resuelto en", null=True, blank=True)

    class Meta:
        verbose_name = "problema"
        verbose_name_plural = "problemas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"PRB-{self.pk}: {self.title}"


class ProblemIncident(models.Model):
    """Vínculo entre un problema y un incidente del servicio de Incidencias."""

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="incidents",
        verbose_name="problema",
    )
    # ID del incidente en el servicio de Incidencias (sin llave foránea entre servicios).
    incident_id = models.CharField("ID de incidente", max_length=64)
    linked_at = models.DateTimeField("vinculado en", auto_now_add=True)

    class Meta:
        verbose_name = "incidente vinculado"
        verbose_name_plural = "incidentes vinculados"
        constraints = [
            models.UniqueConstraint(
                fields=["problem", "incident_id"], name="problem_incident_unique"
            )
        ]

    def __str__(self) -> str:
        return f"PRB-{self.problem_id} ↔ {self.incident_id}"


class KnownError(models.Model):
    """Problema con causa raíz documentada y una solución temporal (workaround)."""

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="known_errors",
        verbose_name="problema",
    )
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción")
    root_cause = models.TextField("causa raíz")
    workaround = models.TextField("solución temporal (workaround)")
    # ID del artículo en el servicio de Knowledge (sin llave foránea entre servicios).
    kb_article_id = models.CharField("ID de artículo KB", max_length=64, blank=True)
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField("creado en", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        verbose_name = "error conocido"
        verbose_name_plural = "errores conocidos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"KE-{self.pk}: {self.title}"
