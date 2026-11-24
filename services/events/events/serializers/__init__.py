"""Serializers de la API de Eventos.
Se reexportan aquí para conservar los imports existentes, p. ej. el hook de
drf-spectacular `events.serializers.contract_required_postprocessing` de settings.py.
"""

from .common import ErrorSerializer, contract_required_postprocessing, nullable_text
from .event import (
    BusinessServiceSerializer,
    EventCreateSerializer,
    EventDetailSerializer,
    EventListItemSerializer,
    EventPageSerializer,
    EventReadSerializer,
)
from .lifecycle import (
    AllowedTransitionsSerializer,
    EventHistoryEntrySerializer,
    EventHistoryPageSerializer,
    EventTransitionSerializer,
    EventUpdateSerializer,
)

__all__ = [
    "AllowedTransitionsSerializer",
    "BusinessServiceSerializer",
    "ErrorSerializer",
    "EventCreateSerializer",
    "EventDetailSerializer",
    "EventHistoryEntrySerializer",
    "EventHistoryPageSerializer",
    "EventListItemSerializer",
    "EventPageSerializer",
    "EventReadSerializer",
    "EventTransitionSerializer",
    "EventUpdateSerializer",
    "contract_required_postprocessing",
    "nullable_text",
]
