"""Clasificación del tipo de evento y vigilancia de advertencias (reglas 1 y 3).

- `classify_event_type`: tipo recibido o, si falta, por configuración (severidad del payload).
- `resolve_recurrence`: umbral N y ventana T (política más específica o valores por defecto).
- `watch_warning`: regla 3, registro y vigilancia; alerta una vez al alcanzar el umbral.
La regla 1 (cierre automático) vive en `events.lifecycle.auto_close_informational`.
"""

import logging
from dataclasses import dataclass

from django.conf import settings

from ..models import (
    ActorType,
    ChangeType,
    EventOrigin,
    EventType,
    RecurrenceAction,
    RecurrencePolicy,
)
from .lifecycle import record_history

logger = logging.getLogger(__name__)

# Severidad (texto libre que mandan las fuentes) -> tipo ITIL. Se puede ampliar o
# sobrescribir con settings.EVENT_SEVERITY_MAP.
DEFAULT_SEVERITY_MAP = {
    "debug": EventType.INFORMATION,
    "info": EventType.INFORMATION,
    "notice": EventType.INFORMATION,
    "warning": EventType.WARNING,
    "warn": EventType.WARNING,
    "error": EventType.EXCEPTION,
    "critical": EventType.EXCEPTION,
    "fatal": EventType.EXCEPTION,
}
DEFAULT_RECURRENCE = {"threshold_count": 3, "window_days": 7}


def classify_event_type(*, origin, declared=None, payload=None) -> EventType:
    """Devuelve el tipo del evento.

    1. Si se declaró un tipo, se respeta (el motor de reglas puede reclasificarlo después).
    2. Si no, se usa la severidad del payload (`settings.EVENT_SEVERITY_KEY`).
    3. Si tampoco hay, por origen: un usuario que reporta algo es EXCEPTION; un evento
       de sistema sin severidad es WARNING (se vigila, no se cierra solo).
    """
    if declared:
        return EventType(declared)
    key = getattr(settings, "EVENT_SEVERITY_KEY", "severity")
    severity_map = {**DEFAULT_SEVERITY_MAP, **getattr(settings, "EVENT_SEVERITY_MAP", {})}
    severity = str((payload or {}).get(key, "")).strip().lower()
    if severity in severity_map:
        return EventType(severity_map[severity])
    return EventType.EXCEPTION if origin == EventOrigin.USER else EventType.WARNING


@dataclass(frozen=True)
class Recurrence:
    threshold_count: int
    window_days: int
    action: str
    source: str


def resolve_recurrence(event) -> Recurrence:
    """Política activa más específica que aplica al evento; si no hay, el valor por defecto."""
    best, best_score = None, -1
    for policy in RecurrencePolicy.objects.filter(is_active=True).order_by("id"):
        if policy.event_type and policy.event_type != event.event_type:
            continue
        if policy.category and policy.category != event.category:
            continue
        if policy.service_id is not None and policy.service_id != event.service_id:
            continue
        score = bool(policy.event_type) + bool(policy.category) + (policy.service_id is not None)
        if score > best_score:
            best, best_score = policy, score
    if best is not None:
        return Recurrence(best.threshold_count, best.window_days, best.action, f"policy:{best.id}")
    default = {**DEFAULT_RECURRENCE, **getattr(settings, "EVENT_RECURRENCE_DEFAULT", {})}
    return Recurrence(
        default["threshold_count"], default["window_days"], RecurrenceAction.WATCH_ALERT, "default"
    )


@dataclass(frozen=True)
class WatchResult:
    watching: bool  # sigue bajo el umbral: solo registro y vigilancia
    threshold_exceeded: bool  # el contador alcanzó o superó el umbral
    alert_raised: bool  # esta llamada generó la alerta (solo una vez)
    recurrence: Recurrence


def watch_warning(event, *, previous_count=0, current_count=None) -> WatchResult | None:
    """Regla 3: advertencia bajo el umbral -> vigilancia; alerta al alcanzar el umbral.

    `previous_count` es el contador antes de esta ocurrencia; así la alerta se emite una
    sola vez, cuando el contador cruza el umbral. `current_count` es el n_eventos_similares de
    la ventana T (si no se indica, se usa `event.occurrence_count`). Aquí no se enruta (eso es
    la regla 7, fase 3): solo se registra la alerta en el historial y en el log.
    """
    if event.event_type != EventType.WARNING:
        return None
    recurrence = resolve_recurrence(event)
    count = event.occurrence_count if current_count is None else current_count
    exceeded = count >= recurrence.threshold_count
    alert = previous_count < recurrence.threshold_count <= count
    if alert:
        details = {
            "occurrence_count": count,
            "threshold_count": recurrence.threshold_count,
            "window_days": recurrence.window_days,
            "policy": recurrence.source,
        }
        record_history(
            event,
            change_type=ChangeType.SYSTEM,
            actor_type=ActorType.RULE,
            actor_ref="R3",
            description=(
                f"Regla 3: umbral de recurrencia alcanzado ({count} ocurrencias; "
                f"umbral {recurrence.threshold_count} en {recurrence.window_days} días)"
            ),
            rule_code="R3",
            metadata=details,
        )
        logger.warning("event_threshold_reached", extra={"event_id": str(event.id), **details})
    return WatchResult(
        watching=not exceeded,
        threshold_exceeded=exceeded,
        alert_raised=alert,
        recurrence=recurrence,
    )
