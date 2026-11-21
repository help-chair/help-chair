"""Pruebas de contrato: schemathesis arma las peticiones desde el esquema.

Carga el esquema que el propio servicio sirve en ``/api/schema/`` y lo ejerce
contra la aplicación en memoria, sin levantar servidor ni base de PostgreSQL.
Por eso entra en ``make test`` y en el pipeline sin pedir nada más.

Solo cubre las rutas implementadas (``/login`` y ``/refresh``). El contrato
escrito a mano declara otras once que todavía no se sirven; de comprobar que
esas dos versiones del contrato concuerdan se encarga ``make openapi``.

Lo que valida en cada ejemplo generado: que el código HTTP que contesta esté
declarado en el esquema, que el cuerpo tenga la forma declarada para ese
código, y que no haya errores 500.
"""

import pytest
import schemathesis
from hypothesis import HealthCheck, settings

from config.wsgi import application

esquema = schemathesis.openapi.from_wsgi("/api/schema/?format=json", application)

# ST202 (positive_data_acceptance) parte de que todo dato que cumpla el esquema
# debe ser aceptado. En un login no se sostiene: un `correo` vacío es un string
# válido para el esquema, porque no declara una longitud mínima, y la API lo
# rechaza con 400, que el contrato sí declara. schemathesis arregló este falso
# positivo para los endpoints que entregan credenciales, pero solo cuando puede
# reconocerlos, y el esquema no marca este como tal. Siguen activos los
# chequeos que importan: sin 500, código declarado y cuerpo con la forma
# declarada para ese código.
esquema.config.checks.positive_data_acceptance.enabled = False

solo_implementadas = esquema.include(path_regex=r"/(login|refresh)$")


@pytest.mark.django_db
@solo_implementadas.parametrize()
@settings(
    max_examples=25,
    deadline=None,
    # La base de pytest-django es una fixture por función y hypothesis avisa de
    # que la reusa entre ejemplos. Aquí da igual: ninguna de estas peticiones
    # llega a crear un usuario.
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_el_servicio_respeta_su_esquema(case):
    case.call_and_validate()
