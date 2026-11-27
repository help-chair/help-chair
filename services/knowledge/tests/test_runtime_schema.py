"""El esquema runtime (/api/schema/) documenta las operaciones de artículos como el contrato."""

import pytest
from drf_spectacular.generators import SchemaGenerator

# operationId del contrato: son parte de la API, no identificadores de código.
OPERATION_IDS = ["listarArticulos", "crearArticulo", "consultarArticulo", "actualizarArticulo"]
# 401 y 403 se documentarán cuando se valide el JWT de Accesos (D-29, articles/access.py).
PENDING_CODES = {"401", "403"}
# q llega con la búsqueda full-text (#275).
PENDING_PARAMETERS = {"q"}


def _operations(schema):
    return {
        operation["operationId"]: operation
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }


def _resolve(schema, node):
    while "$ref" in node:
        node = schema["components"]["schemas"][node["$ref"].rsplit("/", 1)[-1]]
    return node


def _parameters(schema, operation):
    return {
        parameter["name"]: parameter
        for parameter in (_resolve_parameter(schema, p) for p in operation.get("parameters", []))
        if parameter["in"] == "query"
    }


def _resolve_parameter(schema, parameter):
    if "$ref" in parameter:
        return schema["components"]["parameters"][parameter["$ref"].rsplit("/", 1)[-1]]
    return parameter


def _request_schema(schema, operation_id):
    body = _operations(schema)[operation_id]["requestBody"]["content"]["application/json"]
    return _resolve(schema, body["schema"])


@pytest.fixture(scope="module")
def runtime():
    return SchemaGenerator().get_schema(request=None, public=True)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_each_operation_declares_the_contract_status_codes(runtime, contract, operation_id):
    expected = set(_operations(contract)[operation_id]["responses"]) - PENDING_CODES
    declared = {str(code) for code in _operations(runtime)[operation_id]["responses"]}
    assert declared == expected


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_operations_use_the_contract_paths(runtime, contract, operation_id):
    def path_of(schema):
        return next(
            path
            for path, item in schema["paths"].items()
            if any(
                isinstance(op, dict) and op.get("operationId") == operation_id
                for op in item.values()
            )
        )

    assert path_of(runtime) == path_of(contract)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_errors_use_the_error_schema(runtime, operation_id):
    for code, response in _operations(runtime)[operation_id]["responses"].items():
        if str(code)[0] in "45":
            schema = response["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/Error"}


def test_error_schema_matches_the_contract(runtime, contract):
    error = runtime["components"]["schemas"]["Error"]
    expected = contract["components"]["schemas"]["Error"]
    assert set(error["properties"]) == set(expected["properties"])
    assert set(error["required"]) == set(expected["required"])
    assert error["properties"]["campos"]["additionalProperties"]["type"] == "string"


def test_list_parameters_match_the_contract_except_pending_search(runtime, contract):
    declared = _parameters(runtime, _operations(runtime)["listarArticulos"])
    expected = _parameters(contract, _operations(contract)["listarArticulos"])
    assert set(declared) == set(expected) - PENDING_PARAMETERS
    assert set(declared["estado"]["schema"]["enum"]) == set(expected["estado"]["schema"]["enum"])
    for name in ("page", "page_size"):
        contract_schema = expected[name]["schema"]
        assert {k: declared[name]["schema"].get(k) for k in contract_schema} == contract_schema


def test_detail_id_is_a_uuid(runtime):
    detail = runtime["paths"]["/api/knowledge/v1/articulos/{id}/"]
    (parameter,) = [p for p in detail["get"]["parameters"] if p["in"] == "path"]
    assert parameter["schema"] == {"type": "string", "format": "uuid"}


def test_response_has_the_contract_article_fields(runtime, contract):
    expected = contract["components"]["schemas"]["ArticuloBase"]
    success = _operations(runtime)["consultarArticulo"]["responses"]["200"]
    article = _resolve(runtime, success["content"]["application/json"]["schema"])
    assert set(article["properties"]) == set(expected["properties"])
    assert set(article["required"]) == set(expected["required"])


@pytest.mark.parametrize(
    ("operation_id", "component"),
    [("crearArticulo", "ArticuloCrear"), ("actualizarArticulo", "ArticuloActualizar")],
)
def test_request_bodies_have_the_contract_fields(runtime, contract, operation_id, component):
    expected = contract["components"]["schemas"][component]
    body = _request_schema(runtime, operation_id)
    assert set(body["properties"]) == set(expected["properties"])
    assert not body.get("required")


def test_list_is_paginated(runtime, contract):
    success = _operations(runtime)["listarArticulos"]["responses"]["200"]
    paginated = _resolve(runtime, success["content"]["application/json"]["schema"])
    expected = contract["components"]["schemas"]["PaginaArticulos"]["properties"]
    assert set(paginated["properties"]) == set(expected)


def test_create_documents_the_location_header(runtime):
    created = _operations(runtime)["crearArticulo"]["responses"]["201"]
    assert "Location" in created["headers"]
