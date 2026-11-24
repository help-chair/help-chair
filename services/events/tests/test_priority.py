"""Pruebas del cálculo de prioridad: tabla de casos (pura), validación de modificadores,
siembra por defecto (``make seed``) e integración con el registro y el detalle del evento.
"""

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from rest_framework.test import APIClient

from events.models import (
    BusinessService,
    ChangeType,
    Event,
    EventHistory,
    ModifierField,
    Priority,
    PriorityMatrix,
    PriorityModifier,
)
from events.priority import PriorityContext, apply_levels, compute_priority

IMPORTANCE = ModifierField.SERVICE_IMPORTANCE
CATEGORY = ModifierField.EVENT_CATEGORY
TYPE = ModifierField.EVENT_TYPE
COUNT = ModifierField.OCCURRENCE_COUNT


def mod(code, condition_field, condition_value, levels_delta, is_active=True) -> PriorityModifier:
    return PriorityModifier(
        code=code,
        condition_field=condition_field,
        condition_value=condition_value,
        levels_delta=levels_delta,
        is_active=is_active,
    )


CRITICO = mod("servicio-critico", IMPORTANCE, "CRITICAL", 1)
BAJO = mod("servicio-baja-importancia", IMPORTANCE, "LOW", -1)
SEGURIDAD = mod("seguridad", CATEGORY, "SECURITY", 1)
EXCEPCION = mod("excepcion", TYPE, "EXCEPTION", 1)
RECURRENCIA = mod("recurrencia-10", COUNT, "10", 1)
INACTIVO = mod("inactivo", IMPORTANCE, "CRITICAL", 2, is_active=False)
TODOS = [CRITICO, BAJO, SEGURIDAD, EXCEPCION, RECURRENCIA, INACTIVO]


CASOS = [
    pytest.param("P3", [], PriorityContext(), "P3", (), id="sin-modificadores-queda-la-base"),
    pytest.param(
        "P3",
        TODOS,
        PriorityContext(service_importance="CRITICAL"),
        "P2",
        ("servicio-critico",),
        id="servicio-critico-sube-un-nivel",
    ),
    pytest.param(
        "P2",
        TODOS,
        PriorityContext(service_importance="LOW"),
        "P3",
        ("servicio-baja-importancia",),
        id="servicio-baja-importancia-baja-un-nivel",
    ),
    pytest.param(
        "P3",
        TODOS,
        PriorityContext(service_importance="MEDIUM", category="GENERAL", event_type="WARNING"),
        "P3",
        (),
        id="ninguna-condicion-coincide",
    ),
    pytest.param(
        "P4",
        TODOS,
        PriorityContext(service_importance="CRITICAL", category="SECURITY", event_type="EXCEPTION"),
        "P1",
        ("servicio-critico", "seguridad", "excepcion"),
        id="modificadores-se-acumulan",
    ),
    pytest.param(
        "P1",
        TODOS,
        PriorityContext(service_importance="CRITICAL", category="SECURITY"),
        "P1",
        ("servicio-critico", "seguridad"),
        id="tope-superior-p1",
    ),
    pytest.param(
        "P4",
        TODOS,
        PriorityContext(service_importance="LOW"),
        "P4",
        ("servicio-baja-importancia",),
        id="tope-inferior-p4",
    ),
    pytest.param(
        "P3",
        TODOS,
        PriorityContext(service_importance="LOW", category="SECURITY"),
        "P3",
        ("servicio-baja-importancia", "seguridad"),
        id="modificadores-opuestos-se-anulan",
    ),
    pytest.param(
        "P3",
        TODOS,
        PriorityContext(occurrence_count=9),
        "P3",
        (),
        id="recurrencia-bajo-el-minimo",
    ),
    pytest.param(
        "P3",
        TODOS,
        PriorityContext(occurrence_count=10),
        "P2",
        ("recurrencia-10",),
        id="recurrencia-en-el-minimo-sube",
    ),
    pytest.param(
        "P3",
        [INACTIVO],
        PriorityContext(service_importance="CRITICAL"),
        "P3",
        (),
        id="modificador-inactivo-no-aplica",
    ),
    pytest.param(
        "P3",
        [mod("mal-configurado", COUNT, "diez", 1)],
        PriorityContext(occurrence_count=50),
        "P3",
        (),
        id="recurrencia-no-numerica-no-aplica",
    ),
]


@pytest.mark.parametrize("base, modifiers, context, expected, applied", CASOS)
def test_tabla_de_casos(base, modifiers, context, expected, applied):
    result = compute_priority(base, modifiers, context)
    assert result.base == Priority(base)
    assert result.priority == Priority(expected)
    assert result.applied == applied


@pytest.mark.parametrize("base", ["", None])
def test_sin_base_no_hay_prioridad(base):
    result = compute_priority(base, TODOS, PriorityContext(service_importance="CRITICAL"))
    assert result.priority is None
    assert result.applied == ()


@pytest.mark.parametrize(
    "base, levels, expected",
    [
        ("P3", 1, "P2"),
        ("P3", 2, "P1"),
        ("P3", 5, "P1"),
        ("P2", -1, "P3"),
        ("P2", -5, "P4"),
        ("P4", 0, "P4"),
    ],
)
def test_apply_levels_limita_el_rango(base, levels, expected):
    assert apply_levels(base, levels) == Priority(expected)


@pytest.mark.parametrize(
    "modifier",
    [
        mod("cero", IMPORTANCE, "CRITICAL", 0),
        mod("importancia-invalida", IMPORTANCE, "URGENTE", 1),
        mod("categoria-invalida", CATEGORY, "OTRA", 1),
        mod("tipo-invalido", TYPE, "ERROR", 1),
        mod("recurrencia-texto", COUNT, "diez", 1),
        mod("recurrencia-cero", COUNT, "0", 1),
    ],
    ids=lambda m: m.code,
)
def test_modificador_invalido(modifier):
    with pytest.raises(ValidationError):
        modifier.clean()


def test_modificador_valido():
    mod("recurrencia-5", COUNT, "5", 1).clean()
    mod("excepcion", TYPE, "EXCEPTION", 1).clean()


@pytest.mark.django_db
def test_seed_crea_valores_por_defecto_y_es_idempotente():
    call_command("seed_priority")
    call_command("seed_priority")
    assert PriorityMatrix.objects.count() == 9
    assert PriorityModifier.objects.count() == 3
    matrix = {(r.impact, r.urgency): r.priority for r in PriorityMatrix.objects.all()}
    assert matrix[("HIGH", "HIGH")] == "P1"
    assert matrix[("MEDIUM", "MEDIUM")] == "P3"
    assert matrix[("LOW", "LOW")] == "P4"


@pytest.mark.django_db
def test_seed_respeta_la_configuracion_de_la_empresa_salvo_reset():
    call_command("seed_priority")
    PriorityMatrix.objects.filter(impact="LOW", urgency="LOW").update(priority="P3")
    PriorityModifier.objects.filter(code="servicio-critico").update(levels_delta=2)

    call_command("seed_priority")
    assert PriorityMatrix.objects.get(impact="LOW", urgency="LOW").priority == "P3"
    assert PriorityModifier.objects.get(code="servicio-critico").levels_delta == 2

    call_command("seed_priority", reset=True)
    assert PriorityMatrix.objects.get(impact="LOW", urgency="LOW").priority == "P4"
    assert PriorityModifier.objects.get(code="servicio-critico").levels_delta == 1


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seeded(db):
    call_command("seed_priority")


def register(api_client, service=None, **fields):
    body = {
        "origin": "SYSTEM",
        "title": fields.pop("title", "Timeout en pagos"),
        "message": "El servicio no responde",
        **fields,
    }
    if service:
        body["service_code"] = service.code
    return api_client.post("/api/v1/events", body, format="json")


@pytest.mark.parametrize(
    "importance, impact, urgency, expected",
    [
        ("CRITICAL", "MEDIUM", "MEDIUM", "P2"),
        ("HIGH", "MEDIUM", "MEDIUM", "P3"),
        ("LOW", "MEDIUM", "MEDIUM", "P4"),
        ("CRITICAL", "HIGH", "HIGH", "P1"),
        ("LOW", "HIGH", "HIGH", "P2"),
    ],
)
def test_prioridad_segun_importancia_del_servicio_visible_en_detalle(
    api_client, seeded, importance, impact, urgency, expected
):
    service = BusinessService.objects.create(
        code=f"svc-{importance.lower()}", name="Servicio", importance=importance
    )
    created = register(api_client, service, impact=impact, urgency=urgency)
    assert created.status_code == 201
    assert created.json()["priority"] == expected

    detail = api_client.get(f"/api/v1/events/{created.json()['id']}")
    assert detail.status_code == 200
    assert detail.json()["priority"] == expected
    assert detail.json()["service"]["importance"] == importance


def test_sin_impacto_o_urgencia_no_hay_prioridad(api_client, seeded):
    created = register(api_client, impact="HIGH")
    assert created.status_code == 201
    assert created.json()["priority"] is None


def test_historial_guarda_base_y_modificadores_aplicados(api_client, seeded):
    service = BusinessService.objects.create(code="core", name="Core", importance="CRITICAL")
    created = register(api_client, service, impact="MEDIUM", urgency="MEDIUM")
    history = EventHistory.objects.get(event_id=created.json()["id"])
    assert history.metadata["priority"] == {
        "base": "P3",
        "priority": "P2",
        "levels": 1,
        "modifiers": ["servicio-critico"],
    }


def test_recurrencia_recalcula_la_prioridad_y_lo_registra(api_client, seeded):
    PriorityModifier.objects.filter(code="recurrencia-10").update(condition_value="3")
    for _ in range(2):
        response = register(api_client, impact="MEDIUM", urgency="MEDIUM")
        assert response.json()["priority"] == "P3"

    third = register(api_client, impact="MEDIUM", urgency="MEDIUM")
    assert third.status_code == 200
    assert third.json()["occurrence_count"] == 3
    assert third.json()["priority"] == "P2"

    event = Event.objects.get(id=third.json()["id"])
    change = event.history.get(change_type=ChangeType.PRIORITY_CHANGE)
    assert (change.old_value, change.new_value) == ("P3", "P2")
    assert change.metadata["priority"]["modifiers"] == ["recurrencia-10"]

    register(api_client, impact="MEDIUM", urgency="MEDIUM")
    assert event.history.filter(change_type=ChangeType.PRIORITY_CHANGE).count() == 1
