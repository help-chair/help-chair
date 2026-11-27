"""El esquema integrado conserva la forma del contrato, sin implementar su API.

Los modelos usan identificadores en inglés; el contrato conserva los nombres en español. Estas
tablas dicen qué componente y qué propiedad del contrato corresponde a cada modelo y campo.
"""

from pathlib import Path

import pytest
import yaml
from django.db import models

from problems.models import KnownError, Problem, ProblemIncident

CONTRACT_COMPONENTS = {
    Problem: "Problema",
    ProblemIncident: "ProblemaIncidente",
    KnownError: "ErrorConocido",
}


@pytest.fixture(scope="module")
def schemas():
    path = Path(__file__).resolve().parents[3] / "contracts/problems/openapi.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["components"]["schemas"]


@pytest.mark.parametrize(
    ("field", "schema"),
    [("status", "EstadoProblema"), ("priority", "Prioridad"), ("origin", "Origen")],
)
def test_model_choices_match_the_existing_contract(field, schema, schemas):
    assert set(dict(Problem._meta.get_field(field).flatchoices)) == set(schemas[schema]["enum"])


@pytest.mark.parametrize("model", list(CONTRACT_COMPONENTS))
def test_internal_primary_keys_remain_int64(model, schemas):
    assert isinstance(model._meta.pk, models.BigAutoField)
    identifier = schemas[CONTRACT_COMPONENTS[model]]["properties"]["id"]
    assert identifier["type"] == "integer"
    assert identifier["format"] == "int64"


@pytest.mark.parametrize(
    ("model", "field", "contract_property"),
    [
        (Problem, "assignee_id", "asignado_a_id"),
        (ProblemIncident, "incident_id", "incidente_id"),
        (KnownError, "kb_article_id", "articulo_kb_id"),
    ],
)
def test_external_references_remain_text_without_cross_service_relations(
    model, field, contract_property, schemas
):
    reference = model._meta.get_field(field)
    contract = schemas[CONTRACT_COMPONENTS[model]]["properties"][contract_property]
    assert isinstance(reference, models.CharField)
    assert not reference.is_relation
    assert contract["type"] == "string"
    assert reference.max_length == contract["maxLength"]
