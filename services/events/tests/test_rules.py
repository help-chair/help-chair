"""Pruebas parametrizadas de las 9 reglas de destino (TDD).

Especificación: docs/rules.md. Cada caso corresponde a una fila de sus tablas.

El motor (``events.rules.evaluate``) aún es un esqueleto: las pruebas de reglas
quedan ``xfail`` (strict) hasta implementarlo. Al implementarlo, quitar la marca
``engine_pending``.

Orden de evaluación asumido (la primera que coincide es la que se considera):
    4 → 2 → 7 → 8 → 5 → 6 → 3 → 1 → 9
"""

import pytest

from events.models.choices import Destination, EventCategory, EventOrigin, EventType
from events.rules import Decision, EventInput, evaluate

engine_pending = pytest.mark.xfail(
    reason="Motor de reglas pendiente de implementar (TDD, issue #67)",
    raises=NotImplementedError,
    strict=True,
)


def make_event(origin=EventOrigin.SYSTEM, event_type=EventType.INFORMATION, **fields) -> EventInput:
    """Construye un evento con valores por defecto; solo se indica lo relevante."""
    return EventInput(origin=origin, event_type=event_type, **fields)


CASES_BY_RULE = [
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.INFORMATION, action_required=False),
        Decision(1, Destination.LOG_ONLY, EventType.INFORMATION),
        id="rule1-system-informational-log-only",
    ),
    pytest.param(
        make_event(EventOrigin.USER, EventType.EXCEPTION, kb_solution_author="author-1"),
        Decision(2, Destination.SOLUTION_AUTHOR, EventType.INFORMATION),
        id="rule2-user-with-solution-in-kb-goes-to-its-author",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.WARNING, similar_event_count=1, threshold=3),
        Decision(3, Destination.EVENTS, EventType.WARNING),
        id="rule3-warning-below-threshold",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.EXCEPTION, category=EventCategory.SECURITY),
        Decision(4, Destination.ACCESS, EventType.WARNING),
        id="rule4-security-or-credentials",
    ),
    pytest.param(
        make_event(EventOrigin.USER, EventType.INFORMATION, category=EventCategory.REQUEST),
        Decision(5, Destination.REQUESTS, EventType.INFORMATION),
        id="rule5-standard-catalog-request",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.EXCEPTION, category=EventCategory.FAILURE),
        Decision(6, Destination.INCIDENTS, EventType.EXCEPTION),
        id="rule6-failure-degradation-or-outage",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.WARNING, similar_event_count=3, threshold=3),
        Decision(7, Destination.PROBLEMS, EventType.EXCEPTION),
        id="rule7-pattern-repeated-n-times",
    ),
    pytest.param(
        make_event(EventOrigin.USER, EventType.INFORMATION, category=EventCategory.CHANGE),
        Decision(8, Destination.REQUESTS, EventType.INFORMATION),
        id="rule8-requires-configuration-change",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.INFORMATION, action_required=True),
        Decision(9, Destination.INCIDENTS, EventType.EXCEPTION),
        id="rule9-no-rule-matches",
    ),
]

EDGE_CASES = [
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.WARNING, similar_event_count=2, threshold=3),
        Decision(3, Destination.EVENTS, EventType.WARNING),
        id="edge-warning-at-threshold-minus-1-stays-in-rule3",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.WARNING, similar_event_count=3, threshold=3),
        Decision(7, Destination.PROBLEMS, EventType.EXCEPTION),
        id="edge-warning-exactly-at-threshold-goes-to-rule7-and-is-reclassified",
    ),
    pytest.param(
        make_event(
            EventOrigin.SYSTEM,
            EventType.EXCEPTION,
            category=EventCategory.FAILURE,
            similar_event_count=5,
            threshold=3,
        ),
        Decision(7, Destination.PROBLEMS, EventType.EXCEPTION),
        id="edge-repeated-failure-goes-to-problems-not-incidents",
    ),
    pytest.param(
        make_event(
            EventOrigin.USER,
            EventType.EXCEPTION,
            category=EventCategory.SECURITY,
            kb_solution_author="author-1",
        ),
        Decision(4, Destination.ACCESS, EventType.WARNING),
        id="edge-security-with-kb-rule4-wins",
    ),
    pytest.param(
        make_event(
            EventOrigin.SYSTEM,
            EventType.EXCEPTION,
            category=EventCategory.SECURITY,
            similar_event_count=9,
        ),
        Decision(4, Destination.ACCESS, EventType.WARNING),
        id="edge-repeated-security-rule4-wins",
    ),
    pytest.param(
        make_event(
            EventOrigin.USER,
            EventType.EXCEPTION,
            category=EventCategory.FAILURE,
            kb_solution_author="author-1",
        ),
        Decision(2, Destination.SOLUTION_AUTHOR, EventType.INFORMATION),
        id="edge-user-failure-with-kb-solution-goes-to-author",
    ),
    pytest.param(
        make_event(EventOrigin.USER, EventType.INFORMATION),
        Decision(9, Destination.INCIDENTS, EventType.EXCEPTION),
        id="edge-user-informational-without-kb-is-not-rule1",
    ),
    pytest.param(
        make_event(EventOrigin.SYSTEM, EventType.INFORMATION, action_required=True),
        Decision(9, Destination.INCIDENTS, EventType.EXCEPTION),
        id="edge-informational-requiring-action-is-not-rule1",
    ),
    pytest.param(
        make_event(EventOrigin.USER, EventType.EXCEPTION),
        Decision(9, Destination.INCIDENTS, EventType.EXCEPTION),
        id="edge-no-match-manual-triage-via-incidents",
    ),
]


@engine_pending
@pytest.mark.parametrize("event, expected", CASES_BY_RULE)
def test_destination_rule(event, expected):
    assert evaluate(event) == expected


@engine_pending
@pytest.mark.parametrize("event, expected", EDGE_CASES)
def test_edge_cases(event, expected):
    assert evaluate(event) == expected


def test_there_is_at_least_one_case_per_rule():
    """Guardia (no xfail): las 9 reglas deben estar cubiertas por CASES_BY_RULE."""
    covered = {p.values[1].rule for p in CASES_BY_RULE}
    assert covered == set(range(1, 10))


def test_assigned_type_matches_the_rules_table():
    """Guardia (no xfail): columna Tipo de docs/rules.md, una entrada por regla."""
    type_by_rule = {p.values[1].rule: p.values[1].event_type for p in CASES_BY_RULE}
    assert type_by_rule == {
        1: EventType.INFORMATION,
        2: EventType.INFORMATION,
        3: EventType.WARNING,
        4: EventType.WARNING,
        5: EventType.INFORMATION,
        6: EventType.EXCEPTION,
        7: EventType.EXCEPTION,
        8: EventType.INFORMATION,
        9: EventType.EXCEPTION,
    }
