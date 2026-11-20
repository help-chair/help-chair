from django.db import models


class EventOrigin(models.TextChoices):
    USER = "USER", "Usuario"
    SYSTEM = "SYSTEM", "Sistema"


class EventType(models.TextChoices):
    INFORMATION = "INFORMATION", "Información"
    WARNING = "WARNING", "Advertencia"
    EXCEPTION = "EXCEPTION", "Excepción"


class EventCategory(models.TextChoices):
    SECURITY = "SECURITY", "Seguridad"
    REQUEST = "REQUEST", "Petición"
    FAILURE = "FAILURE", "Falla"
    CHANGE = "CHANGE", "Cambio"
    GENERAL = "GENERAL", "General"


class EventState(models.TextChoices):
    NEW = "NEW", "Nuevo"
    ASSIGNED = "ASSIGNED", "Asignado"
    IN_PROGRESS = "IN_PROGRESS", "En proceso"
    ON_HOLD = "ON_HOLD", "En espera"
    RESOLVED = "RESOLVED", "Resuelto"
    CLOSED = "CLOSED", "Cerrado"
    REJECTED = "REJECTED", "Rechazado"
    CANCELLED = "CANCELLED", "Cancelado"
    REOPENED = "REOPENED", "Reabierto"


# Estados en los que el evento ya no está "abierto" (no se deduplica contra ellos).
TERMINAL_STATES = [EventState.CLOSED, EventState.REJECTED, EventState.CANCELLED]

# Transiciones permitidas del ciclo de vida (diagrama 3).
ALLOWED_TRANSITIONS = {
    EventState.NEW: {EventState.ASSIGNED, EventState.REJECTED, EventState.CLOSED},
    EventState.ASSIGNED: {EventState.IN_PROGRESS, EventState.CANCELLED},
    EventState.IN_PROGRESS: {EventState.ON_HOLD, EventState.RESOLVED},
    EventState.ON_HOLD: {EventState.IN_PROGRESS},
    EventState.RESOLVED: {EventState.CLOSED},
    EventState.CLOSED: {EventState.REOPENED},
    EventState.REOPENED: {EventState.ASSIGNED},
    EventState.REJECTED: set(),
    EventState.CANCELLED: set(),
}


class Destination(models.TextChoices):
    """Destino que decide el motor de reglas (docs/rules.md, sección 4)."""

    LOG_ONLY = "LOG_ONLY", "Solo registro"  # regla 1
    SOLUTION_AUTHOR = "SOLUTION_AUTHOR", "Autor de la solución (KB)"  # regla 2
    EVENTS = "EVENTS", "Eventos (registro y vigilancia)"  # regla 3
    ACCESS = "ACCESS", "Accesos / Seguridad"  # regla 4
    REQUESTS = "REQUESTS", "Peticiones"  # reglas 5 y 8
    INCIDENTS = "INCIDENTS", "Incidencias"  # reglas 6 y 9
    PROBLEMS = "PROBLEMS", "Problemas"  # regla 7


class ServiceImportance(models.TextChoices):
    CRITICAL = "CRITICAL", "Crítica"
    HIGH = "HIGH", "Alta"
    MEDIUM = "MEDIUM", "Media"
    LOW = "LOW", "Baja"


class Priority(models.TextChoices):
    CRITICAL = "P1", "Crítica"
    HIGH = "P2", "Alta"
    MEDIUM = "P3", "Media"
    LOW = "P4", "Baja"


class Impact(models.TextChoices):
    HIGH = "HIGH", "Alto"
    MEDIUM = "MEDIUM", "Medio"
    LOW = "LOW", "Bajo"


class Urgency(models.TextChoices):
    HIGH = "HIGH", "Alta"
    MEDIUM = "MEDIUM", "Media"
    LOW = "LOW", "Baja"


class ClosureCode(models.TextChoices):
    AUTO_LOGGED = "AUTO_LOGGED", "Registrado automáticamente"
    KB_RESOLVED = "KB_RESOLVED", "Resuelto por la KB"
    SOLVED = "SOLVED", "Resuelto"
    NOT_APPLICABLE = "NOT_APPLICABLE", "No aplica"


class SourceKind(models.TextChoices):
    SERVICE = "SERVICE", "Servicio"
    WEBHOOK = "WEBHOOK", "Webhook"
    USER_FORM = "USER_FORM", "Formulario de usuario"
    INTERNAL = "INTERNAL", "Interno"


class ChangeType(models.TextChoices):
    STATE_CHANGE = "STATE_CHANGE", "Cambio de estado"
    ASSIGNMENT = "ASSIGNMENT", "Asignación"
    PRIORITY_CHANGE = "PRIORITY_CHANGE", "Cambio de prioridad"
    CLASSIFICATION = "CLASSIFICATION", "Clasificación"
    ROUTING = "ROUTING", "Enrutamiento"
    NOTE = "NOTE", "Nota"
    SYSTEM = "SYSTEM", "Sistema"


class ActorType(models.TextChoices):
    USER = "USER", "Usuario"
    SYSTEM = "SYSTEM", "Sistema"
    RULE = "RULE", "Regla"
