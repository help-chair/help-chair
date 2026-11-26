"""Ciclo de vida del problema: única fuente de verdad de las transiciones permitidas."""

from problems.models import Problema

State = Problema.Estado

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    State.REGISTRADO: frozenset({State.EN_ANALISIS, State.CERRADO}),
    State.EN_ANALISIS: frozenset({State.CAUSA_IDENTIFICADA, State.REGISTRADO}),
    State.CAUSA_IDENTIFICADA: frozenset({State.ERROR_CONOCIDO, State.RESUELTO, State.EN_ANALISIS}),
    State.ERROR_CONOCIDO: frozenset({State.RESUELTO, State.EN_ANALISIS}),
    # resuelto -> en_analisis es reabrir el problema.
    State.RESUELTO: frozenset({State.CERRADO, State.EN_ANALISIS}),
    State.CERRADO: frozenset(),
}

# Estados destino que exigen una causa raíz no vacía.
ROOT_CAUSE_REQUIRED_STATES = frozenset({State.CAUSA_IDENTIFICADA, State.ERROR_CONOCIDO})


def is_valid_transition(current: str, target: str) -> bool:
    """Pasar al mismo estado nunca es una transición válida."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def is_reopening(current: str, target: str) -> bool:
    return current == State.RESUELTO and target == State.EN_ANALISIS


def invalid_transition_message(current: str, target: str) -> str:
    return f"No se puede pasar de {current} a {target}."
