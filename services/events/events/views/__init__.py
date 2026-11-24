"""Vistas de la API de Eventos (se reexportan para `events.urls`)."""

from .events import EventDetailView, EventListCreateView
from .lifecycle import EventHistoryView, EventTransitionsView

__all__ = [
    "EventDetailView",
    "EventHistoryView",
    "EventListCreateView",
    "EventTransitionsView",
]
