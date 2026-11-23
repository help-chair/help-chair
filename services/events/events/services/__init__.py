"""Lógica de negocio del servicio de Eventos (sin HTTP).

- registration: registro, huella y deduplicación.
- classification: tipo del evento y regla 3 (vigilancia de advertencias).
- lifecycle: transiciones, asignación y regla 1 (cierre automático).
- updates: reclasificación y PATCH de gestión.
- priority: matriz de prioridad y SLA.
"""

from .classification import classify_event_type, resolve_recurrence, watch_warning
from .lifecycle import (
    EventConflict,
    InvalidTransition,
    TransitionValidationError,
    allowed_transitions,
    assign_event,
    auto_close_informational,
    record_history,
    transition_event,
)
from .registration import compute_fingerprint, register_event
from .updates import reclassify_event, update_event

__all__ = [
    "EventConflict",
    "InvalidTransition",
    "TransitionValidationError",
    "allowed_transitions",
    "assign_event",
    "auto_close_informational",
    "classify_event_type",
    "compute_fingerprint",
    "reclassify_event",
    "record_history",
    "register_event",
    "resolve_recurrence",
    "transition_event",
    "update_event",
    "watch_warning",
]
