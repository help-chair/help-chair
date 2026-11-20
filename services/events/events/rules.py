"""Motor de reglas de destino de Eventos (ESQUELETO).

Especificación: ``docs/rules.md``. Define la entrada (``EventInput``), la salida
(``Decision``) y la firma de ``evaluate``. El vocabulario sale de
``events.models.choices`` para que el motor y los modelos usen los mismos valores.
La lógica de las 9 reglas se implementa después (TDD): ver ``tests/test_rules.py``.
"""

from dataclasses import dataclass

from events.models.choices import Destination, EventCategory, EventOrigin, EventType


@dataclass(frozen=True)
class EventInput:
    """Datos mínimos que el motor necesita para decidir (docs/rules.md, sección 4)."""

    origin: EventOrigin
    event_type: EventType
    action_required: bool = False
    category: EventCategory | None = None
    kb_solution_author: str | None = None
    similar_event_count: int = 0
    # N: umbral de recurrencia.
    threshold: int = 3


@dataclass(frozen=True)
class Decision:
    rule: int
    destination: Destination
    event_type: EventType


def evaluate(event: EventInput) -> Decision:
    """Devuelve la regla aplicada y el destino del evento."""
    raise NotImplementedError("Motor de reglas pendiente de implementar")
