"""Ayudas para crear eventos en las pruebas."""

import uuid

from events.models import Event, EventOrigin, EventType


def make_event(**overrides) -> Event:
    data = {
        "origin": EventOrigin.SYSTEM,
        "event_type": EventType.INFORMATION,
        "title": "Evento de prueba",
        "message": "mensaje",
        "fingerprint": uuid.uuid4().hex * 2,  # 64 caracteres, distinto en cada evento
    }
    data.update(overrides)
    return Event.objects.create(**data)
