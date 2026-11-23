from pathlib import Path

import pytest
import yaml
from drf_spectacular.generators import SchemaGenerator
from openapi_spec_validator import validate

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"
EVENTS_OPENAPI = CONTRACTS / "events" / "openapi.yaml"


@pytest.fixture(scope="module")
def contract_schema():
    return yaml.safe_load(EVENTS_OPENAPI.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def generated_schema():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    validate(schema)
    return schema


def _resolved_contract_schema(schema, node):
    if "$ref" in node:
        name = node["$ref"].rsplit("/", 1)[-1]
        return _resolved_contract_schema(schema, schema["components"]["schemas"][name])

    if "allOf" in node:
        merged = {"required": [], "properties": {}}
        for part in node["allOf"]:
            resolved = _resolved_contract_schema(schema, part)
            merged["required"].extend(resolved.get("required", []))
            merged["properties"].update(resolved.get("properties", {}))
        for key, value in node.items():
            if key not in ("allOf", "required", "properties"):
                merged[key] = value
        merged["required"] = list(dict.fromkeys(merged["required"]))
        return merged

    return node


def _schema_traits(schema, node):
    if "oneOf" in node:
        nullable = node.get("nullable", False)
        enum = None
        traits = {"type": None, "format": None, "nullable": nullable}
        for branch in node["oneOf"]:
            resolved = _schema_traits(schema, branch)
            if resolved["nullable"] or resolved["type"] is None:
                nullable = True
                continue
            traits.update(
                {
                    "type": resolved["type"],
                    "format": resolved["format"],
                    "enum": resolved["enum"],
                }
            )
        traits["nullable"] = nullable
        return traits

    node = _resolved_contract_schema(schema, node)
    nullable = bool(node.get("nullable", False))
    enum = node.get("enum")
    if enum is not None:
        nullable = nullable or None in enum
        enum = [value for value in enum if value is not None]
    return {
        "type": node.get("type") or ("string" if enum is not None else None),
        "format": node.get("format"),
        "nullable": nullable,
        "enum": enum,
    }


def test_generated_schema_is_valid(generated_schema):
    validate(generated_schema)


def test_generated_schema_matches_frozen_v1_contract(generated_schema, contract_schema):
    assert generated_schema["info"]["version"] == contract_schema["info"]["version"] == "1.0.0"
    assert generated_schema["servers"] == contract_schema["servers"]
    assert set(generated_schema["paths"]) == set(contract_schema["paths"])
    assert (
        generated_schema["components"]["securitySchemes"]
        == contract_schema["components"]["securitySchemes"]
    )

    for path in generated_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "operationId" in operation:
                assert operation["security"] == [{"bearerAuth": []}, {"apiKeyAuth": []}]


def test_issue_paths_and_operation_ids(generated_schema, contract_schema):
    generated_paths = generated_schema["paths"]
    contract_paths = contract_schema["paths"]

    for path, methods in (
        ("/events", {"get", "post"}),
        ("/events/{id}", {"get"}),
    ):
        assert path in generated_paths
        assert path in contract_paths
        for method in methods:
            assert method in generated_paths[path]
            assert method in contract_paths[path]

    assert generated_paths["/events"]["get"]["operationId"] == "listEvents"
    assert generated_paths["/events"]["post"]["operationId"] == "registerEvent"
    assert generated_paths["/events/{id}"]["get"]["operationId"] == "getEvent"


def test_list_query_parameters(generated_schema):
    parameters = generated_schema["paths"]["/events"]["get"].get("parameters", [])
    names = {parameter["name"] for parameter in parameters if parameter["in"] == "query"}
    expected = {
        "state",
        "event_type",
        "category",
        "priority",
        "origin",
        "service_code",
        "assigned_to_ref",
        "open",
        "created_from",
        "created_to",
        "search",
        "ordering",
        "limit",
        "offset",
    }
    assert names == expected


def test_list_query_constraints_match_view_validation(generated_schema):
    parameters = {
        parameter["name"]: parameter["schema"]
        for parameter in generated_schema["paths"]["/events"]["get"]["parameters"]
        if parameter["in"] == "query"
    }

    assert parameters["created_from"]["format"] == "date-time"
    assert parameters["created_to"]["format"] == "date-time"
    assert parameters["search"]["maxLength"] == 100
    assert parameters["limit"]["minimum"] == 1
    assert parameters["limit"]["maximum"] == 200
    assert parameters["offset"]["minimum"] == 0
    assert set(parameters["ordering"]["enum"]) == {
        "created_at",
        "-created_at",
        "last_seen_at",
        "-last_seen_at",
        "priority",
        "-priority",
        "resolution_due_at",
        "-resolution_due_at",
    }


@pytest.mark.parametrize(
    ("path", "method", "expected_codes"),
    [
        ("/events", "get", {"200", "422"}),
        ("/events", "post", {"200", "201", "422"}),
        ("/events/{id}", "get", {"200", "404"}),
    ],
)
def test_issue_response_codes(generated_schema, path, method, expected_codes):
    responses = set(generated_schema["paths"][path][method]["responses"])
    assert expected_codes <= responses


@pytest.mark.parametrize(
    "component",
    ["EventCreate", "EventRead", "EventListItem", "EventDetail", "EventPage", "Error"],
)
def test_component_properties_and_required(generated_schema, contract_schema, component):
    generated = generated_schema["components"]["schemas"][component]

    contract_node = contract_schema["components"]["schemas"][component]
    contract = _resolved_contract_schema(contract_schema, contract_node)

    assert set(generated.get("properties", {})) == set(contract.get("properties", {})), component
    assert set(generated.get("required", [])) == set(contract.get("required", [])), component


@pytest.mark.parametrize(
    ("component", "fields"),
    [
        ("EventCreate", ["origin", "title", "message"]),
        ("EventRead", ["service_code", "source_name", "impact", "urgency", "priority"]),
        ("EventListItem", ["priority", "service_code", "destination", "assigned_to_ref"]),
        ("EventDetail", ["routing", "service"]),
        ("EventPage", ["count", "next", "previous", "results"]),
        ("Error", ["code", "detail", "fields"]),
    ],
)
def test_component_scalar_types_and_nulllability(
    generated_schema,
    contract_schema,
    component,
    fields,
):
    contract_node = contract_schema["components"]["schemas"][component]
    contract = _resolved_contract_schema(contract_schema, contract_node)
    generated = generated_schema["components"]["schemas"][component]

    for field in fields:
        if field not in contract["properties"] or field not in generated["properties"]:
            continue
        contract_traits = _schema_traits(contract_schema, contract["properties"][field])
        generated_traits = _schema_traits(generated_schema, generated["properties"][field])

        if contract_traits["type"]:
            assert generated_traits["type"] == contract_traits["type"], (component, field)
        if contract_traits["format"]:
            assert generated_traits["format"] == contract_traits["format"], (component, field)
        assert generated_traits["nullable"] == contract_traits["nullable"], (component, field)
