"""Ayudas para crear eventos en las pruebas."""

import json
import uuid
from pathlib import Path

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


# --- sobre común de mensajes (contracts/messages/event-envelope.json) ------------------
ENVELOPE_SCHEMA = (
    Path(__file__).resolve().parents[3] / "contracts" / "messages" / "event-envelope.json"
)


def envelope_errors(data: dict) -> list[str]:
    """Errores de validación del sobre contra el contrato (lista vacía = conforme)."""
    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads(ENVELOPE_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(data)]
