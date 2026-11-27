"""Factories de factory_boy compartidas por las pruebas de la API (problemas, incidentes, KE)."""

import factory
from django.utils import timezone

from problems.models import Problem, ProblemIncident
from problems.states import ROOT_CAUSE_REQUIRED_STATES

# Estados a los que solo se llega habiendo documentado la causa raíz.
_STATES_WITH_ROOT_CAUSE = ROOT_CAUSE_REQUIRED_STATES | {Problem.Status.RESOLVED}


class ProblemFactory(factory.django.DjangoModelFactory):
    """Problema coherente: ``root_cause`` y ``resolved_at`` se derivan de ``status``."""

    class Meta:
        model = Problem

    title = factory.Sequence(lambda n: f"Problema de prueba {n}")
    description = factory.LazyAttribute(lambda o: f"Descripción de {o.title.lower()}.")
    status = Problem.Status.REGISTERED
    priority = Problem.Priority.MEDIUM
    origin = Problem.Origin.MANUAL
    root_cause = factory.LazyAttribute(
        lambda o: "Causa raíz documentada." if o.status in _STATES_WITH_ROOT_CAUSE else ""
    )
    assignee_id = ""
    resolved_at = factory.LazyAttribute(
        lambda o: timezone.now() if o.status == Problem.Status.RESOLVED else None
    )


class ProblemIncidentFactory(factory.django.DjangoModelFactory):
    """Vínculo problema–incidente; el ID del incidente es texto libre, como en Incidencias."""

    class Meta:
        model = ProblemIncident

    problem = factory.SubFactory(ProblemFactory)
    incident_id = factory.Sequence(lambda n: f"INC-{n}")
