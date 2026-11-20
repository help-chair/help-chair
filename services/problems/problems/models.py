"""Modelos de Gestión de Problemas (ITIL v4): problemas, incidentes vinculados y errores conocidos.

Los IDs de otros servicios (Accesos, Incidencias, Knowledge) se guardan como texto, sin llaves
foráneas: cada servicio tiene su propia base de datos (database per service).
"""

from django.db import models


class Problema(models.Model):
    """Causa subyacente de uno o más incidentes."""

    class Estado(models.TextChoices):
        REGISTRADO = "registrado", "Registrado"
        EN_ANALISIS = "en_analisis", "En análisis"
        CAUSA_IDENTIFICADA = "causa_identificada", "Causa identificada"
        ERROR_CONOCIDO = "error_conocido", "Error conocido"
        RESUELTO = "resuelto", "Resuelto"
        CERRADO = "cerrado", "Cerrado"

    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"
        CRITICA = "critica", "Crítica"

    class Origen(models.TextChoices):
        MANUAL = "manual", "Manual"
        PATRON = "patron", "Patrón detectado"

    titulo = models.CharField("título", max_length=200)
    descripcion = models.TextField("descripción")
    estado = models.CharField(
        "estado", max_length=20, choices=Estado.choices, default=Estado.REGISTRADO
    )
    prioridad = models.CharField(
        "prioridad", max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA
    )
    # manual: lo registró una persona; patron: se detectó por incidentes repetidos.
    origen = models.CharField(
        "origen", max_length=10, choices=Origen.choices, default=Origen.MANUAL
    )
    causa_raiz = models.TextField("causa raíz", blank=True)
    # ID del usuario en el servicio de Accesos (sin llave foránea entre servicios).
    asignado_a_id = models.CharField("asignado a (ID de usuario)", max_length=64, blank=True)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)
    resuelto_en = models.DateTimeField("resuelto en", null=True, blank=True)

    class Meta:
        verbose_name = "problema"
        verbose_name_plural = "problemas"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"PRB-{self.pk}: {self.titulo}"


class ProblemaIncidente(models.Model):
    """Vínculo entre un problema y un incidente del servicio de Incidencias."""

    problema = models.ForeignKey(
        Problema,
        on_delete=models.CASCADE,
        related_name="incidentes",
        verbose_name="problema",
    )
    # ID del incidente en el servicio de Incidencias (sin llave foránea entre servicios).
    incidente_id = models.CharField("ID de incidente", max_length=64)
    vinculado_en = models.DateTimeField("vinculado en", auto_now_add=True)

    class Meta:
        verbose_name = "incidente vinculado"
        verbose_name_plural = "incidentes vinculados"
        constraints = [
            models.UniqueConstraint(
                fields=["problema", "incidente_id"], name="problema_incidente_unico"
            )
        ]

    def __str__(self) -> str:
        return f"PRB-{self.problema_id} ↔ {self.incidente_id}"


class ErrorConocido(models.Model):
    """Problema con causa raíz documentada y una solución temporal (workaround)."""

    problema = models.ForeignKey(
        Problema,
        on_delete=models.CASCADE,
        related_name="errores_conocidos",
        verbose_name="problema",
    )
    titulo = models.CharField("título", max_length=200)
    descripcion = models.TextField("descripción")
    causa_raiz = models.TextField("causa raíz")
    workaround = models.TextField("solución temporal (workaround)")
    # ID del artículo en el servicio de Knowledge (sin llave foránea entre servicios).
    articulo_kb_id = models.CharField("ID de artículo KB", max_length=64, blank=True)
    activo = models.BooleanField("activo", default=True)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        verbose_name = "error conocido"
        verbose_name_plural = "errores conocidos"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"KE-{self.pk}: {self.titulo}"
