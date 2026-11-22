"""Motor de reglas de destino de Eventos.

Decide el destino de un evento y la regla aplicada, sin llamadas de red ni acceso a BD.
Las reglas se evalúan en RULE_ORDER y gana la primera que coincide (ver docs/reglas.md).
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class Origin(StrEnum):
    SYSTEM = "sistema"
    USER = "usuario"


class EventType(StrEnum):
    INFORMATIVE = "informativo"
    WARNING = "advertencia"
    EXCEPTION = "excepcion"


class Category(StrEnum):
    SECURITY = "seguridad"
    CATALOG_REQUEST = "solicitud_catalogo"
    FAILURE = "falla"
    CHANGE = "cambio"


class Destination(StrEnum):
    LOG = "registro"
    SOLUTION_AUTHOR = "autor_solucion"
    EVENT = "eventos"
    ACCESS = "accesos"
    REQUEST = "peticiones"
    INCIDENT = "incidencias"
    PROBLEM = "problemas"
    CHANGE = "cambios"
    MANUAL_TRIAGE = "triage_manual"


@dataclass(frozen=True)
class Event:
    origin: Origin
    event_type: EventType
    requires_action: bool = False
    category: Category | None = None
    kb_solution_author: str | None = None
    repetitions: int = 0
    threshold: int = 3


@dataclass(frozen=True)
class Decision:
    rule: int
    destination: Destination
    event_type: EventType


@dataclass(frozen=True)
class Rule:
    number: int
    matches: Callable[[Event], bool]
    destination: Destination
    event_type: EventType


RULES: dict[int, Rule] = {
    rule.number: rule
    for rule in (
        Rule(
            1,
            lambda e: (
                e.origin == Origin.SYSTEM
                and e.event_type == EventType.INFORMATIVE
                and not e.requires_action
            ),
            Destination.LOG,
            EventType.INFORMATIVE,
        ),
        Rule(
            2,
            lambda e: e.origin == Origin.USER and bool(e.kb_solution_author),
            Destination.SOLUTION_AUTHOR,
            EventType.INFORMATIVE,
        ),
        Rule(
            3,
            lambda e: e.event_type == EventType.WARNING and e.repetitions < e.threshold,
            Destination.EVENT,
            EventType.WARNING,
        ),
        Rule(
            4,
            lambda e: e.category == Category.SECURITY,
            Destination.ACCESS,
            EventType.WARNING,
        ),
        Rule(
            5,
            lambda e: e.category == Category.CATALOG_REQUEST,
            Destination.REQUEST,
            EventType.INFORMATIVE,
        ),
        Rule(
            6,
            lambda e: e.category == Category.FAILURE,
            Destination.INCIDENT,
            EventType.EXCEPTION,
        ),
        Rule(
            7,
            lambda e: e.repetitions >= e.threshold,
            Destination.PROBLEM,
            EventType.EXCEPTION,
        ),
        Rule(
            8,
            lambda e: e.category == Category.CHANGE,
            Destination.CHANGE,
            EventType.INFORMATIVE,
        ),
        Rule(
            9,
            lambda e: True,
            Destination.MANUAL_TRIAGE,
            EventType.EXCEPTION,
        ),
    )
}

RULE_ORDER: tuple[int, ...] = (4, 2, 7, 8, 5, 6, 3, 1, 9)


def evaluate(event: Event) -> Decision:
    """Devuelve la regla aplicada y el destino del evento."""
    for number in RULE_ORDER:
        rule = RULES[number]
        if rule.matches(event):
            return Decision(rule.number, rule.destination, rule.event_type)
    raise AssertionError("La regla 9 coincide siempre")
