"""Cálculo de prioridad de eventos (ITIL v4, Monitoring and Event Management).

La prioridad base sale de la matriz impacto × urgencia (``PriorityMatrix``) y se ajusta con los
modificadores activos (``PriorityModifier``): cada uno suma ``levels_delta`` niveles (+1 sube de
P3 a P2) cuando el evento cumple su condición. El resultado se limita al rango P1–P4.
``compute_priority`` es pura; ``resolve_priority`` lee la configuración de la empresa en la BD.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

from .models import ModifierField, Priority, PriorityMatrix, PriorityModifier

PRIORITY_LEVELS: tuple[Priority, ...] = (
    Priority.CRITICAL,
    Priority.HIGH,
    Priority.MEDIUM,
    Priority.LOW,
)


@dataclass(frozen=True)
class PriorityContext:
    service_importance: str | None = None
    category: str | None = None
    event_type: str | None = None
    occurrence_count: int = 1


@dataclass(frozen=True)
class PriorityResult:
    base: Priority | None
    priority: Priority | None
    levels: int = 0
    applied: tuple[str, ...] = field(default_factory=tuple)

    def as_metadata(self) -> dict:
        return {
            "base": self.base.value if self.base else None,
            "priority": self.priority.value if self.priority else None,
            "levels": self.levels,
            "modifiers": list(self.applied),
        }


def apply_levels(base: str, levels: int) -> Priority:
    index = PRIORITY_LEVELS.index(Priority(base)) - levels
    return PRIORITY_LEVELS[min(max(index, 0), len(PRIORITY_LEVELS) - 1)]


def modifier_applies(modifier: PriorityModifier, context: PriorityContext) -> bool:
    value = modifier.condition_value
    match modifier.condition_field:
        case ModifierField.SERVICE_IMPORTANCE:
            return context.service_importance == value
        case ModifierField.EVENT_CATEGORY:
            return context.category == value
        case ModifierField.EVENT_TYPE:
            return context.event_type == value
        case ModifierField.OCCURRENCE_COUNT:
            return value.isdigit() and context.occurrence_count >= int(value)
    return False


def compute_priority(
    base: str | None,
    modifiers: Iterable[PriorityModifier],
    context: PriorityContext,
) -> PriorityResult:
    if not base:
        return PriorityResult(base=None, priority=None)
    applied = [m for m in modifiers if m.is_active and modifier_applies(m, context)]
    levels = sum(m.levels_delta for m in applied)
    return PriorityResult(
        base=Priority(base),
        priority=apply_levels(base, levels),
        levels=levels,
        applied=tuple(m.code for m in applied),
    )


def resolve_priority(impact: str, urgency: str, context: PriorityContext) -> PriorityResult:
    if not (impact and urgency):
        return PriorityResult(base=None, priority=None)
    base = (
        PriorityMatrix.objects.filter(impact=impact, urgency=urgency)
        .values_list("priority", flat=True)
        .first()
    )
    modifiers = PriorityModifier.objects.filter(is_active=True).order_by("code")
    return compute_priority(base, modifiers, context)
