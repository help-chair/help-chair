"""El esquema integrado conserva la forma del contrato, sin implementar su API."""

from pathlib import Path

import pytest
import yaml
from django.db import models

from problems.models import ErrorConocido, Problema, ProblemaIncidente


@pytest.fixture(scope="module")
def schemas():
    path = Path(__file__).resolve().parents[3] / "contracts/problems/openapi.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["components"]["schemas"]


@pytest.mark.parametrize(
    ("field", "schema"),
    [("estado", "EstadoProblema"), ("prioridad", "Prioridad"), ("origen", "Origen")],
)
def test_model_choices_match_the_existing_contract(field, schema, schemas):
    assert set(dict(Problema._meta.get_field(field).flatchoices)) == set(schemas[schema]["enum"])


@pytest.mark.parametrize("model", [Problema, ProblemaIncidente, ErrorConocido])
def test_internal_primary_keys_remain_int64(model, schemas):
    assert isinstance(model._meta.pk, models.BigAutoField)
    identifier = schemas[model.__name__]["properties"]["id"]
    assert identifier["type"] == "integer"
    assert identifier["format"] == "int64"


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (Problema, "asignado_a_id"),
        (ProblemaIncidente, "incidente_id"),
        (ErrorConocido, "articulo_kb_id"),
    ],
)
def test_external_references_remain_text_without_cross_service_relations(model, field, schemas):
    reference = model._meta.get_field(field)
    contract = schemas[model.__name__]["properties"][field]
    assert isinstance(reference, models.CharField)
    assert not reference.is_relation
    assert contract["type"] == "string"
    assert reference.max_length == contract["maxLength"]
