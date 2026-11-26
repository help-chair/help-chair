"""Ciclo de vida del problema: única fuente de verdad de las transiciones permitidas."""

from problems.models import Problem

Status = Problem.Status

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    Status.REGISTERED: frozenset({Status.IN_ANALYSIS, Status.CLOSED}),
    Status.IN_ANALYSIS: frozenset({Status.ROOT_CAUSE_IDENTIFIED, Status.REGISTERED}),
    Status.ROOT_CAUSE_IDENTIFIED: frozenset(
        {Status.KNOWN_ERROR, Status.RESOLVED, Status.IN_ANALYSIS}
    ),
    Status.KNOWN_ERROR: frozenset({Status.RESOLVED, Status.IN_ANALYSIS}),
    # resuelto -> en_analisis es reabrir el problema.
    Status.RESOLVED: frozenset({Status.CLOSED, Status.IN_ANALYSIS}),
    Status.CLOSED: frozenset(),
}

# Estados destino que exigen una causa raíz no vacía.
ROOT_CAUSE_REQUIRED_STATES = frozenset({Status.ROOT_CAUSE_IDENTIFIED, Status.KNOWN_ERROR})


def is_valid_transition(current: str, target: str) -> bool:
    """Pasar al mismo estado nunca es una transición válida."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def is_reopening(current: str, target: str) -> bool:
    return current == Status.RESOLVED and target == Status.IN_ANALYSIS


def invalid_transition_message(current: str, target: str) -> str:
    return f"No se puede pasar de {current} a {target}."
