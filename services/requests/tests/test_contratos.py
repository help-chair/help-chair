from io import StringIO
from pathlib import Path

import pytest
import schemathesis
import yaml
from django.core.management import call_command
from hypothesis import HealthCheck, settings
from openapi_spec_validator import validate
from schemathesis.checks import (
    content_type_conformance,
    not_a_server_error,
    response_headers_conformance,
    response_schema_conformance,
    status_code_conformance,
)

from config.wsgi import application

CONTRATO_PATH = (
    Path(__file__).resolve().parents[3] / "contracts" / "requests" / "openapi.yaml"
)

schema = schemathesis.openapi.from_path(str(CONTRATO_PATH))

CHECKS_CONTRATO = [
    not_a_server_error,
    status_code_conformance,
    content_type_conformance,
    response_headers_conformance,
    response_schema_conformance,
]


def test_contrato_openapi_es_valido():
    spec = yaml.safe_load(CONTRATO_PATH.read_text(encoding="utf-8"))
    validate(spec)


def test_contrato_sincronizado_con_codigo():
    salida = StringIO()
    call_command("spectacular", stdout=salida)
    generado = yaml.safe_load(salida.getvalue())
    guardado = yaml.safe_load(CONTRATO_PATH.read_text(encoding="utf-8"))
    assert generado == guardado, (
        "contracts/requests/openapi.yaml está desactualizado; "
        "regenéralo con `python manage.py spectacular`."
    )


@pytest.mark.django_db(transaction=True)
@schema.parametrize()
@settings(
    max_examples=15,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_api_cumple_contrato(case):
    case.call_and_validate(app=application, checks=CHECKS_CONTRATO)