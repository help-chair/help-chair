"""El esquema runtime (/api/schema/) documenta las mismas respuestas que el contrato revisado."""

from pathlib import Path

import pytest
import yaml
from drf_spectacular.generators import SchemaGenerator

# operationId del contrato: son parte de la API, no identificadores de código.
OPERATION_IDS = [
    "listProblemas",
    "createProblema",
    "getProblema",
    "updateProblema",
    "changeProblemaEstado",
]
# 401 se documentará cuando se valide el JWT de Accesos (Fase 3).
PENDING_CODES = {"401"}


def _operations(schema):
    return {
        operation["operationId"]: operation
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }


@pytest.fixture(scope="module")
def runtime():
    return SchemaGenerator().get_schema(request=None, public=True)


@pytest.fixture(scope="module")
def contract():
    path = Path(__file__).resolve().parents[3] / "contracts/problems/openapi.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_each_operation_declares_the_contract_status_codes(runtime, contract, operation_id):
    expected = set(_operations(contract)[operation_id]["responses"]) - PENDING_CODES
    declared = {str(code) for code in _operations(runtime)[operation_id]["responses"]}
    assert declared == expected


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_errors_use_the_error_schema(runtime, operation_id):
    responses = _operations(runtime)[operation_id]["responses"]
    for code, response in responses.items():
        if str(code).startswith("4"):
            schema = response["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/Error"}


def test_error_schema_matches_the_contract(runtime, contract):
    error = runtime["components"]["schemas"]["Error"]
    expected = contract["components"]["schemas"]["Error"]
    assert set(error["properties"]) == set(expected["properties"])
    assert set(error["required"]) == set(expected["required"])
    assert error["properties"]["campos"]["additionalProperties"]["type"] == "string"


def test_list_is_still_paginated(runtime):
    success = _operations(runtime)["listProblemas"]["responses"]["200"]
    reference = success["content"]["application/json"]["schema"]["$ref"]
    paginated = runtime["components"]["schemas"][reference.rsplit("/", 1)[-1]]
    assert {"count", "next", "previous", "results"} <= set(paginated["properties"])
