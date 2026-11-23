"""Matriz de prioridad impacto × urgencia (issue #120)."""

import pytest

from incidents.models import Incident
from incidents.priority import calculate_priority


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        ("alto", "alta", "P1"),
        ("alto", "media", "P2"),
        ("alto", "baja", "P3"),
        ("medio", "alta", "P2"),
        ("medio", "media", "P3"),
        ("medio", "baja", "P4"),
        ("bajo", "alta", "P3"),
        ("bajo", "media", "P4"),
        ("bajo", "baja", "P4"),
    ],
)
def test_matriz_de_prioridad(impact, urgency, expected):
    assert calculate_priority(impact, urgency) == expected


def test_valores_invalidos_lanzan_error():
    with pytest.raises(ValueError):
        calculate_priority("enorme", "alta")


@pytest.mark.django_db
def test_la_prioridad_se_calcula_al_guardar():
    incident = Incident.objects.create(
        title="Correo caído", impact="alto", urgency="alta", reported_by="usr-1"
    )
    assert incident.priority == "P1"


@pytest.mark.django_db
def test_la_prioridad_se_recalcula_si_cambia_la_urgencia():
    incident = Incident.objects.create(
        title="Correo caído", impact="alto", urgency="alta", reported_by="usr-1"
    )
    incident.urgency = "baja"
    incident.save()
    incident.refresh_from_db()
    assert incident.priority == "P3"


@pytest.mark.django_db
def test_la_prioridad_se_recalcula_con_update_fields():
    incident = Incident.objects.create(
        title="Correo caído", impact="alto", urgency="alta", reported_by="usr-1"
    )
    incident.impact = "bajo"
    incident.save(update_fields=["impact"])
    incident.refresh_from_db()
    assert incident.priority == "P3"
