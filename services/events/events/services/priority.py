"""Prioridad (matriz impacto x urgencia) y SLA de un evento."""

from datetime import timedelta

from ..models import PriorityMatrix, SlaPolicy


def resolve_priority(impact, urgency) -> str:
    """Prioridad de la matriz para (impacto, urgencia); "" si falta alguno o no hay celda."""
    if not (impact and urgency):
        return ""
    row = PriorityMatrix.objects.filter(impact=impact, urgency=urgency).first()
    return row.priority if row else ""


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
