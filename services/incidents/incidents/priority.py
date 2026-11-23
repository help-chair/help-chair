"""Matriz de prioridad ITIL v4: prioridad = impacto × urgencia (issue #120).

| Impacto \\ Urgencia | Alta       | Media    | Baja     |
|---------------------|------------|----------|----------|
| Alto                | P1 Crítica | P2 Alta  | P3 Media |
| Medio               | P2 Alta    | P3 Media | P4 Baja  |
| Bajo                | P3 Media   | P4 Baja  | P4 Baja  |
"""

from django.db import models


class Impact(models.TextChoices):
    """A cuántos usuarios o servicios afecta."""

    HIGH = "alto", "Alto"
    MEDIUM = "medio", "Medio"
    LOW = "bajo", "Bajo"


class Urgency(models.TextChoices):
    """Qué tan rápido hace falta resolverlo."""

    HIGH = "alta", "Alta"
    MEDIUM = "media", "Media"
    LOW = "baja", "Baja"


class Priority(models.TextChoices):
    P1 = "P1", "P1 - Crítica"
    P2 = "P2", "P2 - Alta"
    P3 = "P3", "P3 - Media"
    P4 = "P4", "P4 - Baja"


PRIORITY_MATRIX: dict[tuple[str, str], str] = {
    (Impact.HIGH, Urgency.HIGH): Priority.P1,
    (Impact.HIGH, Urgency.MEDIUM): Priority.P2,
    (Impact.HIGH, Urgency.LOW): Priority.P3,
    (Impact.MEDIUM, Urgency.HIGH): Priority.P2,
    (Impact.MEDIUM, Urgency.MEDIUM): Priority.P3,
    (Impact.MEDIUM, Urgency.LOW): Priority.P4,
    (Impact.LOW, Urgency.HIGH): Priority.P3,
    (Impact.LOW, Urgency.MEDIUM): Priority.P4,
    (Impact.LOW, Urgency.LOW): Priority.P4,
}


def calculate_priority(impact: str, urgency: str) -> str:
    """Devuelve la prioridad (P1–P4) para un impacto y una urgencia válidos."""
    try:
        return PRIORITY_MATRIX[(impact, urgency)]
    except KeyError:
        raise ValueError(f"Impacto o urgencia inválidos: {impact!r}, {urgency!r}") from None
