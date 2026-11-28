"""
Pruebas del motor de reglas (``events.rules.evaluate``): un caso por regla y casos de borde.

Orden de evaluación asumido (la primera que coincide es la que se considera):
    4 → 2 → 7 → 8 → 5 → 6 → 3 → 1 → 9
"""

import pytest

from events.rules import Category, Decision, Destination, Event, EventType, Origin, evaluate


def evt(origin=Origin.SYSTEM, event_type=EventType.INFORMATIVE, **fields) -> Event:
    """Construye un evento con valores por defecto; solo se indica lo relevante."""
    return Event(origin=origin, event_type=event_type, **fields)


CASOS_POR_REGLA = [
    pytest.param(
        evt(Origin.SYSTEM, EventType.INFORMATIVE, requires_action=False),
        Decision(1, Destination.LOG, EventType.INFORMATIVE),
        id="regla1-informativo-de-sistema-solo-registro",
    ),
    pytest.param(
        evt(Origin.USER, EventType.EXCEPTION, kb_solution_author="autor_kb"),
        Decision(2, Destination.SOLUTION_AUTHOR, EventType.INFORMATIVE),
        id="regla2-usuario-con-solucion-en-kb",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.WARNING, repetitions=1, threshold=3),
        Decision(3, Destination.EVENT, EventType.WARNING),
        id="regla3-advertencia-bajo-umbral",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.EXCEPTION, category=Category.SECURITY),
        Decision(4, Destination.ACCESS, EventType.WARNING),
        id="regla4-seguridad-o-credenciales",
    ),
    pytest.param(
        evt(Origin.USER, EventType.INFORMATIVE, category=Category.CATALOG_REQUEST),
        Decision(5, Destination.REQUEST, EventType.INFORMATIVE),
        id="regla5-solicitud-estandar-del-catalogo",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.EXCEPTION, category=Category.FAILURE),
        Decision(6, Destination.INCIDENT, EventType.EXCEPTION),
        id="regla6-falla-degradacion-o-interrupcion",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.WARNING, repetitions=3, threshold=3),
        Decision(7, Destination.PROBLEM, EventType.EXCEPTION),
        id="regla7-patron-repetido-n-veces",
    ),
    pytest.param(
        evt(Origin.USER, EventType.INFORMATIVE, category=Category.CHANGE),
        Decision(8, Destination.CHANGE, EventType.INFORMATIVE),
        id="regla8-requiere-cambio-de-configuracion",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.INFORMATIVE, requires_action=True),
        Decision(9, Destination.MANUAL_TRIAGE, EventType.EXCEPTION),
        id="regla9-ninguna-coincide",
    ),
]


CASOS_DE_BORDE = [
    pytest.param(
        evt(Origin.SYSTEM, EventType.WARNING, repetitions=2, threshold=3),
        Decision(3, Destination.EVENT, EventType.WARNING),
        id="borde-advertencia-en-umbral-menos-1-sigue-en-regla3",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.WARNING, repetitions=3, threshold=3),
        Decision(7, Destination.PROBLEM, EventType.EXCEPTION),
        id="borde-advertencia-justo-en-umbral-pasa-a-regla7-y-se-reclasifica",
    ),
    pytest.param(
        evt(
            Origin.SYSTEM,
            EventType.EXCEPTION,
            category=Category.FAILURE,
            repetitions=5,
            threshold=3,
        ),
        Decision(7, Destination.PROBLEM, EventType.EXCEPTION),
        id="borde-falla-repetida-va-a-problemas-no-a-incidencias",
    ),
    pytest.param(
        evt(
            Origin.USER,
            EventType.EXCEPTION,
            category=Category.SECURITY,
            kb_solution_author="autor_kb",
        ),
        Decision(4, Destination.ACCESS, EventType.WARNING),
        id="borde-seguridad-con-kb-gana-regla4",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.EXCEPTION, category=Category.SECURITY, repetitions=9),
        Decision(4, Destination.ACCESS, EventType.WARNING),
        id="borde-seguridad-repetida-gana-regla4",
    ),
    pytest.param(
        evt(
            Origin.USER,
            EventType.EXCEPTION,
            category=Category.FAILURE,
            kb_solution_author="autor_kb",
        ),
        Decision(2, Destination.SOLUTION_AUTHOR, EventType.INFORMATIVE),
        id="borde-falla-de-usuario-con-kb-autoservicio-primero",
    ),
    pytest.param(
        evt(Origin.USER, EventType.INFORMATIVE),
        Decision(9, Destination.MANUAL_TRIAGE, EventType.EXCEPTION),
        id="borde-informativo-de-usuario-sin-kb-no-es-regla1",
    ),
    pytest.param(
        evt(Origin.SYSTEM, EventType.INFORMATIVE, requires_action=True),
        Decision(9, Destination.MANUAL_TRIAGE, EventType.EXCEPTION),
        id="borde-informativo-que-requiere-accion-no-es-regla1",
    ),
    pytest.param(
        evt(Origin.USER, EventType.EXCEPTION),
        Decision(9, Destination.MANUAL_TRIAGE, EventType.EXCEPTION),
        id="borde-sin-coincidencia-triage-manual",
    ),
]


@pytest.mark.parametrize("event, expected", CASOS_POR_REGLA)
def test_regla_de_destino(event, expected):
    assert evaluate(event) == expected


@pytest.mark.parametrize("event, expected", CASOS_DE_BORDE)
def test_casos_de_borde(event, expected):
    assert evaluate(event) == expected


def test_regla4_conserva_excepcion_de_seguridad_de_accesos():
    event = evt(
        Origin.SYSTEM,
        EventType.EXCEPTION,
        category=Category.SECURITY,
        security_exception=True,
    )

    assert evaluate(event) == Decision(4, Destination.ACCESS, EventType.EXCEPTION)


def test_informativo_de_seguridad_no_se_reclasifica_por_regla4():
    event = evt(
        Origin.SYSTEM,
        EventType.INFORMATIVE,
        category=Category.SECURITY,
        requires_action=False,
    )

    assert evaluate(event) == Decision(1, Destination.LOG, EventType.INFORMATIVE)


def test_hay_al_menos_un_caso_por_cada_regla():
    """Guardia: las 9 reglas deben estar cubiertas por CASOS_POR_REGLA."""
    cubiertas = {p.values[1].rule for p in CASOS_POR_REGLA}
    assert cubiertas == set(range(1, 10))


def test_el_tipo_asignado_coincide_con_la_tabla_de_reglas():
    """Guardia: columna Tipo de docs/reglas.md, una entrada por regla."""
    tipo_por_regla = {p.values[1].rule: p.values[1].event_type for p in CASOS_POR_REGLA}
    assert tipo_por_regla == {
        1: EventType.INFORMATIVE,
        2: EventType.INFORMATIVE,
        3: EventType.WARNING,
        4: EventType.WARNING,
        5: EventType.INFORMATIVE,
        6: EventType.EXCEPTION,
        7: EventType.EXCEPTION,
        8: EventType.INFORMATIVE,
        9: EventType.EXCEPTION,
    }


def test_cada_destino_tiene_una_regla():
    """Guardia: los 9 destinos del issue se alcanzan con las 9 reglas, uno por regla."""
    destinos = {p.values[1].destination for p in CASOS_POR_REGLA}
    assert destinos == set(Destination)
    assert len(Destination) == 9
