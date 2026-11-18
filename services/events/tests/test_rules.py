"""
El motor (``events.rules.evaluar``) aún es un esqueleto: las pruebas de reglas quedan
``xfail`` (strict) hasta implementarlo. Al implementarlo, quitar la marca ``motor_pendiente``.

Orden de evaluación asumido (la primera que coincide es la que se considera):
    4 → 2 → 7 → 8 → 5 → 6 → 3 → 1 → 9
"""

import pytest
from events.rules import Categoria, Decision, Destino, Evento, Origen, Tipo, evaluar

motor_pendiente = pytest.mark.xfail(
    reason="Motor de reglas pendiente de implementar (TDD, issue #67)",
    raises=NotImplementedError,
    strict=True,
)


def evt(origen=Origen.SISTEMA, tipo=Tipo.INFORMATIVO, **campos) -> Evento:
    """Construye un evento con valores por defecto; solo se indica lo relevante."""
    return Evento(origen=origen, tipo=tipo, **campos)


CASOS_POR_REGLA = [
    pytest.param(
        evt(Origen.SISTEMA, Tipo.INFORMATIVO, requiere_accion=False),
        Decision(1, Destino.REGISTRO, Tipo.INFORMATIVO),
        id="regla1-informativo-de-sistema-solo-registro",
    ),
    pytest.param(
        evt(Origen.USUARIO, Tipo.EXCEPCION, autor_solucion_kb="autor_kb"),
        Decision(2, Destino.AUTOR_SOLUCION, Tipo.INFORMATIVO),
        id="regla2-usuario-con-solucion-en-kb",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.ADVERTENCIA, repeticiones=1, umbral=3),
        Decision(3, Destino.EVENTOS, Tipo.ADVERTENCIA),
        id="regla3-advertencia-bajo-umbral",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.EXCEPCION, categoria=Categoria.SEGURIDAD),
        Decision(4, Destino.ACCESOS, Tipo.ADVERTENCIA),
        id="regla4-seguridad-o-credenciales",
    ),
    pytest.param(
        evt(Origen.USUARIO, Tipo.INFORMATIVO, categoria=Categoria.SOLICITUD_CATALOGO),
        Decision(5, Destino.PETICIONES, Tipo.INFORMATIVO),
        id="regla5-solicitud-estandar-del-catalogo",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.EXCEPCION, categoria=Categoria.FALLA),
        Decision(6, Destino.INCIDENCIAS, Tipo.EXCEPCION),
        id="regla6-falla-degradacion-o-interrupcion",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.ADVERTENCIA, repeticiones=3, umbral=3),
        Decision(7, Destino.PROBLEMAS, Tipo.EXCEPCION),
        id="regla7-patron-repetido-n-veces",
    ),
    pytest.param(
        evt(Origen.USUARIO, Tipo.INFORMATIVO, categoria=Categoria.CAMBIO),
        Decision(8, Destino.PETICIONES, Tipo.INFORMATIVO),
        id="regla8-requiere-cambio-de-configuracion",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.INFORMATIVO, requiere_accion=True),
        Decision(9, Destino.INCIDENCIAS, Tipo.EXCEPCION),
        id="regla9-ninguna-coincide",
    ),
]


CASOS_DE_BORDE = [
    pytest.param(
        evt(Origen.SISTEMA, Tipo.ADVERTENCIA, repeticiones=2, umbral=3),
        Decision(3, Destino.EVENTOS, Tipo.ADVERTENCIA),
        id="borde-advertencia-en-umbral-menos-1-sigue-en-regla3",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.ADVERTENCIA, repeticiones=3, umbral=3),
        Decision(7, Destino.PROBLEMAS, Tipo.EXCEPCION),
        id="borde-advertencia-justo-en-umbral-pasa-a-regla7-y-se-reclasifica",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.EXCEPCION, categoria=Categoria.FALLA, repeticiones=5, umbral=3),
        Decision(7, Destino.PROBLEMAS, Tipo.EXCEPCION),
        id="borde-falla-repetida-va-a-problemas-no-a-incidencias",
    ),
    pytest.param(
        evt(
            Origen.USUARIO,
            Tipo.EXCEPCION,
            categoria=Categoria.SEGURIDAD,
            autor_solucion_kb="autor_kb",
        ),
        Decision(4, Destino.ACCESOS, Tipo.ADVERTENCIA),
        id="borde-seguridad-con-kb-gana-regla4",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.EXCEPCION, categoria=Categoria.SEGURIDAD, repeticiones=9),
        Decision(4, Destino.ACCESOS, Tipo.ADVERTENCIA),
        id="borde-seguridad-repetida-gana-regla4",
    ),
    pytest.param(
        evt(
            Origen.USUARIO, Tipo.EXCEPCION, categoria=Categoria.FALLA, autor_solucion_kb="autor_kb"
        ),
        Decision(2, Destino.AUTOR_SOLUCION, Tipo.INFORMATIVO),
        id="borde-falla-de-usuario-con-kb-autoservicio-primero",
    ),
    pytest.param(
        evt(Origen.USUARIO, Tipo.INFORMATIVO),
        Decision(9, Destino.INCIDENCIAS, Tipo.EXCEPCION),
        id="borde-informativo-de-usuario-sin-kb-no-es-regla1",
    ),
    pytest.param(
        evt(Origen.SISTEMA, Tipo.INFORMATIVO, requiere_accion=True),
        Decision(9, Destino.INCIDENCIAS, Tipo.EXCEPCION),
        id="borde-informativo-que-requiere-accion-no-es-regla1",
    ),
    pytest.param(
        evt(Origen.USUARIO, Tipo.EXCEPCION),
        Decision(9, Destino.INCIDENCIAS, Tipo.EXCEPCION),
        id="borde-sin-coincidencia-triage-via-incidencias",
    ),
]

@motor_pendiente
@pytest.mark.parametrize("evento, esperado", CASOS_POR_REGLA)
def test_regla_de_destino(evento, esperado):
    assert evaluar(evento) == esperado


@motor_pendiente
@pytest.mark.parametrize("evento, esperado", CASOS_DE_BORDE)
def test_casos_de_borde(evento, esperado):
    assert evaluar(evento) == esperado


def test_hay_al_menos_un_caso_por_cada_regla():
    """Guardia (no xfail): las 9 reglas deben estar cubiertas por CASOS_POR_REGLA."""
    cubiertas = {p.values[1].regla for p in CASOS_POR_REGLA}
    assert cubiertas == set(range(1, 10))


def test_el_tipo_asignado_coincide_con_la_tabla_de_reglas():
    """Guardia (no xfail): columna Tipo de docs/reglas.md, una entrada por regla."""
    tipo_por_regla = {p.values[1].regla: p.values[1].tipo for p in CASOS_POR_REGLA}
    assert tipo_por_regla == {
        1: Tipo.INFORMATIVO,
        2: Tipo.INFORMATIVO,
        3: Tipo.ADVERTENCIA,
        4: Tipo.ADVERTENCIA,
        5: Tipo.INFORMATIVO,
        6: Tipo.EXCEPCION,
        7: Tipo.EXCEPCION,
        8: Tipo.INFORMATIVO,
        9: Tipo.EXCEPCION,
    }
