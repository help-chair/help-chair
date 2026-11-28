import uuid

from django.db import models


class ServicioSolicitable(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Peticion(models.Model):
    class Estado(models.TextChoices):
        NUEVO = "nuevo", "Nuevo"
        ASIGNADO = "asignado", "Asignado"
        EN_PROCESO = "en_proceso", "En proceso"
        RESUELTO = "resuelto", "Resuelto"
        CERRADO = "cerrado", "Cerrado"
        REABIERTO = "reabierto", "Reabierto"
        CANCELADO = "cancelado", "Cancelado"

    class Tipo(models.TextChoices):
        SERVICIO = "servicio", "Servicio"
        CAMBIO = "cambio", "Cambio"

    TRANSICIONES = {
        Estado.NUEVO: {Estado.ASIGNADO, Estado.CANCELADO},
        Estado.ASIGNADO: {Estado.EN_PROCESO, Estado.CANCELADO},
        Estado.EN_PROCESO: {Estado.RESUELTO, Estado.CANCELADO},
        Estado.RESUELTO: {Estado.CERRADO, Estado.REABIERTO},
        Estado.REABIERTO: {Estado.ASIGNADO, Estado.EN_PROCESO},
        Estado.CERRADO: set(),
        Estado.CANCELADO: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.SERVICIO)
    servicio = models.ForeignKey(
        ServicioSolicitable, on_delete=models.PROTECT, related_name="peticiones"
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.NUEVO)

    # Referencias a otros servicios: solo IDs, nunca llaves foráneas entre BD
    solicitante_id = models.BigIntegerField()
    asignado_a_id = models.BigIntegerField(null=True, blank=True)
    evento_id = models.BigIntegerField(null=True, blank=True)

    motivo_cancelacion = models.CharField(max_length=255, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)
    cerrada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creada"]
        indexes = [models.Index(fields=["estado", "asignado_a_id"])]

    def __str__(self):
        return f"{self.titulo} ({self.get_estado_display()})"

    def puede_pasar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES[self.estado]