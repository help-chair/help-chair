"""El ciclo de vida implementado coincide con contracts/events/openapi.yaml.

Complementa a test_openapi_contract.py (que cubre registro, listado y detalle).
"""

from pathlib import Path

import pytest
import yaml
from drf_spectacular.generators import SchemaGenerator
from openapi_spec_validator import validate

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "contracts" / "events" / "openapi.yaml"
API_PREFIX = "/api/v1"

# (ruta del contrato, método) -> (operationId, códigos de respuesta que debe documentar)
OPERATIONS = {
    ("/events/{id}", "patch"): ("updateEvent", {"200", "404", "409", "422"}),
    ("/events/{id}/transitions", "get"): ("listAllowedTransitions", {"200", "404"}),
    ("/events/{id}/transitions", "post"): ("transitionEvent", {"200", "404", "409", "422"}),
    ("/events/{id}/history", "get"): ("listEventHistory", {"200", "404"}),
}
COMPONENTS = [
    "EventTransition",
    "AllowedTransitions",
    "EventUpdate",
    "EventHistoryEntry",
    "EventHistoryPage",
]


@pytest.fixture(scope="module")
def contract():
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def generated():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    validate(schema)
    return schema


@pytest.mark.parametrize(("path", "method"), list(OPERATIONS))
def test_operation_matches_the_contract(generated, contract, path, method):
    operation_id, codes = OPERATIONS[(path, method)]

    assert contract["paths"][path][method]["operationId"] == operation_id
    implemented = generated["paths"][API_PREFIX + path][method]
    assert implemented["operationId"] == operation_id
    assert codes <= set(implemented["responses"])


@pytest.mark.parametrize("name", COMPONENTS)
def test_component_matches_the_contract(generated, contract, name):
    expected = contract["components"]["schemas"][name]
    actual = generated["components"]["schemas"][name]

    assert set(actual.get("properties", {})) == set(expected.get("properties", {})), name
    assert set(actual.get("required", [])) == set(expected.get("required", [])), name


def test_contract_documents_assignment_and_automatic_closing(contract):
    """Quien cambie el comportamiento debe actualizar el contrato (lo leen otros equipos)."""
    patch_text = contract["paths"]["/events/{id}"]["patch"]["description"]
    assert "ASSIGNED" in patch_text
    assert "no** se cambia aquí" not in patch_text
    assert "CLOSED" in contract["paths"]["/events"]["post"]["description"]
