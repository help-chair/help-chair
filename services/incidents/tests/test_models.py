"""Modelo, estados y datos de ejemplo (issues #119 y #121)."""

import pytest
from django.core.management import call_command

from incidents.models import TRANSITIONS, Incident, Status
from incidents.priority import calculate_priority

pytestmark = pytest.mark.django_db


def crear(**extra) -> Incident:
    data = {"title": "Nómina no abre", "impact": "medio", "urgency": "alta", "reported_by": "u1"}
    return Incident.objects.create(**{**data, **extra})


def test_un_incidente_nuevo_queda_en_estado_nuevo():
    assert crear().status == Status.NEW


def test_codigo_legible():
    incident = crear()
    assert incident.code == f"INC-{incident.pk:06d}"
    assert str(incident).startswith("INC-")


def test_todos_los_estados_tienen_transiciones_definidas():
    assert set(TRANSITIONS) == set(Status.values)


@pytest.mark.parametrize("final", [Status.CLOSED, Status.REJECTED, Status.CANCELLED])
def test_los_estados_finales_no_tienen_salida(final):
    assert TRANSITIONS[final] == frozenset()


def test_resolver_y_cerrar_guardan_la_fecha():
    incident = crear(status=Status.RESOLVED)
    assert incident.resolved_at is not None
    incident.status = Status.CLOSED
    incident.save()
    assert incident.closed_at is not None


def test_reabrir_borra_la_fecha_de_resolucion():
    incident = crear(status=Status.RESOLVED)
    incident.status = Status.REOPENED
    incident.save()
    assert incident.resolved_at is None


def test_datos_de_ejemplo_cargan_y_respetan_la_matriz():
    call_command("loaddata", "incidentes_ejemplo", verbosity=0)
    incidents = Incident.objects.all()
    assert incidents.count() == 4
    for incident in incidents:
        assert incident.priority == calculate_priority(incident.impact, incident.urgency)
