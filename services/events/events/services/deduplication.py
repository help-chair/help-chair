"""Deduplicación de eventos: coincidencia exacta por huella, similitud opcional y conteo.

Etapa 1 (siempre): mismo `fingerprint` en un evento abierto -> misma incidencia. La restricción
  única parcial `uq_event_open_fingerprint` y el bloqueo de fila hacen que sea segura ante
  concurrencia.
Etapa 2 (opcional, apagada por defecto): similitud Jaro-Winkler con salvaguardas contra el
  *over-merging* (ver `similarity.py`). Se activa con EVENT_FUZZY_ENABLED.
`similar_event_count` entrega el n_eventos_similares de las reglas 3 y 7.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ..models import TERMINAL_STATES, Event, EventCategory, EventOccurrence, MatchKind
from .classification import resolve_recurrence
from .fingerprint import normalize_text
from .similarity import FuzzyConfig, compare_messages


@dataclass(frozen=True)
class DedupMatch:
    event: Event
    kind: str
    similarity: float | None = None


def _setting(name, default):
    return getattr(settings, name, default)


def fuzzy_enabled() -> bool:
    return bool(_setting("EVENT_FUZZY_ENABLED", False))


def fuzzy_config() -> FuzzyConfig:
    return FuzzyConfig(
        threshold=float(_setting("EVENT_FUZZY_THRESHOLD", 0.95)),
        token_threshold=float(_setting("EVENT_FUZZY_TOKEN_THRESHOLD", 0.88)),
        max_diff_tokens=int(_setting("EVENT_FUZZY_MAX_DIFF_TOKENS", 1)),
        min_length=int(_setting("EVENT_FUZZY_MIN_LENGTH", 20)),
    )


def find_open_event_by_fingerprint(fingerprint: str) -> Event | None:
    """Evento abierto con esa huella, bloqueando la fila (select_for_update)."""
    return (
        Event.objects.select_for_update()
        .filter(fingerprint=fingerprint)
        .exclude(state__in=TERMINAL_STATES)
        .first()
    )


def _comparable(title: str, message: str) -> str:
    return f"{normalize_text(title)} | {normalize_text(message)}"


def find_fuzzy_match(
    *, event_type, origin, category, source, service, title, message, event_dt
) -> DedupMatch | None:
    """Evento abierto casi idéntico (errata o variación mínima), o None.

    Salvaguardas: solo mismo tipo/origen/categoría/fuente/servicio; solo tipos configurados
    (WARNING e INFORMATION por defecto); nunca SECURITY; solo eventos vistos dentro de la
    ventana T; como máximo EVENT_FUZZY_MAX_CANDIDATES candidatos.
    """
    if not fuzzy_enabled():
        return None
    allowed_types = _setting("EVENT_FUZZY_TYPES", ["WARNING", "INFORMATION"])
    if str(event_type) not in allowed_types or category == EventCategory.SECURITY:
        return None

    window_days = resolve_recurrence(
        Event(event_type=event_type, category=category, service=service)
    ).window_days
    candidates = (
        Event.objects.filter(
            event_type=event_type,
            origin=origin,
            category=category,
            source=source,
            service=service,
            last_seen_at__gte=event_dt - timedelta(days=window_days),
        )
        .exclude(state__in=TERMINAL_STATES)
        .order_by("-last_seen_at")[: int(_setting("EVENT_FUZZY_MAX_CANDIDATES", 50))]
    )
    wanted = _comparable(title, message)
    config = fuzzy_config()
    best, best_score = None, 0.0
    for candidate in candidates:
        result = compare_messages(wanted, _comparable(candidate.title, candidate.message), config)
        if result.is_duplicate and result.score > best_score:
            best, best_score = candidate, result.score
    if best is None:
        return None
    locked = (
        Event.objects.select_for_update()
        .filter(pk=best.pk)
        .exclude(state__in=TERMINAL_STATES)
        .first()
    )
    return DedupMatch(locked, MatchKind.FUZZY, best_score) if locked else None


def similar_event_count(event, *, window_days: int | None = None, now=None) -> int:
    """n_eventos_similares: ocurrencias con la huella del evento dentro de la ventana T.

    Cuenta también las de eventos anteriores ya cerrados (un patrón repetido es repetido aunque
    cada vez se haya cerrado). T sale de la política de recurrencia (o del valor por defecto).
    """
    if window_days is None:
        window_days = resolve_recurrence(event).window_days
    since = (now or timezone.now()) - timedelta(days=window_days)
    return EventOccurrence.objects.filter(
        fingerprint=event.fingerprint, occurred_at__gte=since
    ).count()
