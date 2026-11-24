"""Contexto de prioridad y SLA de un evento.

El cálculo de la prioridad (matriz impacto x urgencia + modificadores) vive en
`events/priority.py`. Aquí solo se arma el contexto desde un evento y se resuelve el SLA.
"""

from datetime import timedelta

from ..models import SlaPolicy
from ..priority import PriorityContext


def priority_context(event) -> PriorityContext:
    """Contexto del motor de prioridad a partir del estado actual del evento."""
    return PriorityContext(
        service_importance=event.service.importance if event.service else None,
        category=event.category,
        event_type=event.event_type,
        occurrence_count=event.occurrence_count,
    )


def resolve_sla(service, priority, base_dt):
    """(política, vence respuesta, vence resolución). La del servicio gana a la general."""
    if not priority:
        return None, None, None
    policy = None
    if service:
        policy = SlaPolicy.objects.filter(service=service, priority=priority).first()
    if not policy:
        policy = SlaPolicy.objects.filter(service__isnull=True, priority=priority).first()
    if not policy:
        return None, None, None
    return (
        policy,
        base_dt + timedelta(minutes=policy.response_minutes),
        base_dt + timedelta(minutes=policy.resolution_minutes),
    )
