"""Factories de factory_boy compartidas por las pruebas de la API (problemas, incidentes, KE)."""

import factory
from django.utils import timezone

from problems.models import Problema
from problems.states import ROOT_CAUSE_REQUIRED_STATES

# Estados a los que solo se llega habiendo documentado la causa raíz.
_STATES_WITH_ROOT_CAUSE = ROOT_CAUSE_REQUIRED_STATES | {Problema.Estado.RESUELTO}


class ProblemFactory(factory.django.DjangoModelFactory):
    """Problema coherente con su estado: causa raíz y ``resuelto_en`` se derivan de ``estado``."""

    class Meta:
        model = Problema

    titulo = factory.Sequence(lambda n: f"Problema de prueba {n}")
    descripcion = factory.LazyAttribute(lambda o: f"Descripción de {o.titulo.lower()}.")
    estado = Problema.Estado.REGISTRADO
    prioridad = Problema.Prioridad.MEDIA
    origen = Problema.Origen.MANUAL
    causa_raiz = factory.LazyAttribute(
        lambda o: "Causa raíz documentada." if o.estado in _STATES_WITH_ROOT_CAUSE else ""
    )
    asignado_a_id = ""
    resuelto_en = factory.LazyAttribute(
        lambda o: timezone.now() if o.estado == Problema.Estado.RESUELTO else None
    )
