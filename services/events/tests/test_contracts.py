"""Valida los contratos v1 de Eventos y el sobre común de mensajes (JSON Schema)."""

import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"
OPENAPI = CONTRACTS / "events" / "openapi.yaml"
ENVELOPE = CONTRACTS / "messages" / "event-envelope.json"

pytestmark = pytest.mark.skipif(
    not (OPENAPI.exists() and ENVELOPE.exists()),
    reason="contracts/ no está disponible (checkout parcial)",
)

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def openapi() -> dict:
    return yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def envelope_schema() -> dict:
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def envelope_validator(envelope_schema) -> Draft202012Validator:
    return Draft202012Validator(envelope_schema, format_checker=FormatChecker())


def _find_nullable_with_allof(node, path="#"):
    """Busca `allOf` + `nullable: true` en el mismo nivel: en OpenAPI 3.0 no admite null."""
    if isinstance(node, dict):
        if node.get("nullable") is True and "allOf" in node:
            yield path
        for key, value in node.items():
            yield from _find_nullable_with_allof(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _find_nullable_with_allof(value, f"{path}/{index}")


def test_openapi_is_valid(openapi):
    validate(openapi)  # lanza una excepción con el detalle si hay errores


def test_operation_ids_are_unique(openapi):
    ids = [
        op["operationId"]
        for item in openapi["paths"].values()
        for method, op in item.items()
        if method in HTTP_METHODS
    ]
    assert len(ids) == len(set(ids))


def test_openapi_declares_events_v1(openapi):
    assert openapi["info"]["version"] == "1.0.0"
    assert openapi["info"]["title"] == "Help-Chair Events Service API (Contrato v1)"
    assert "Contrato de Eventos v1 congelado" in openapi["info"]["description"]
    assert openapi["servers"] == [
        {"url": "/api/events/v1", "description": "API Gateway (externo)"},
        {"url": "/api/v1", "description": "Servicio directo (interno)"},
    ]

    paths = openapi["paths"]
    assert set(paths) == {
        "/events",
        "/events/{id}",
        "/events/{id}/transitions",
        "/events/{id}/history",
    }
    assert {"get", "post"} <= set(paths["/events"])
    assert {"get", "patch"} == set(paths["/events/{id}"])


def test_openapi_declares_gateway_security(openapi):
    security_schemes = openapi["components"]["securitySchemes"]
    assert security_schemes["bearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    assert security_schemes["apiKeyAuth"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }

    expected_security = [{"bearerAuth": []}, {"apiKeyAuth": []}]
    for path in openapi["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "operationId" in operation:
                assert operation["security"] == expected_security


def test_openapi_has_no_nullable_combined_with_allof(openapi):
    """Prism y los validadores rechazan null ahí (cabecera sl-violations); usa un enum con null."""
    assert list(_find_nullable_with_allof(openapi)) == []


def test_envelope_is_a_valid_json_schema(envelope_schema):
    Draft202012Validator.check_schema(envelope_schema)


def test_envelope_requires_the_agreed_fields(envelope_schema):
    required = set(envelope_schema["required"])
    assert {"id", "type", "origin", "timestamp", "version", "payload"} <= required


def test_envelope_examples_are_valid(envelope_schema, envelope_validator):
    for example in envelope_schema["examples"]:
        assert list(envelope_validator.iter_errors(example)) == []


@pytest.mark.parametrize(
    ("case", "change"),
    [
        (
            "LOG_ONLY destination never leaves Events",
            lambda m: m["payload"].update(destination="LOG_ONLY"),
        ),
        ("rule code outside R1-R9", lambda m: m["payload"].update(rule_code="R10")),
        ("fingerprint is not a SHA-256", lambda m: m["payload"].update(fingerprint="abc")),
        ("missing occurred_at", lambda m: m.pop("occurred_at")),
        ("unknown field in the envelope", lambda m: m.update(extra=1)),
        ("event.routed is only published by events", lambda m: m.update(origin="access")),
        ("nonexistent priority", lambda m: m["payload"].update(priority="URGENT")),
        ("malformed type", lambda m: m.update(type="EventRouted")),
    ],
)
def test_envelope_rejects_invalid_messages(envelope_schema, envelope_validator, case, change):
    message = copy.deepcopy(envelope_schema["examples"][0])
    change(message)
    assert list(envelope_validator.iter_errors(message)), case
