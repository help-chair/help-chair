from pathlib import Path

import pytest
import yaml
from openapi_schema_validator import OAS30ReadValidator, oas30_format_checker
from rest_framework.test import APIClient

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "contracts/knowledge/openapi.yaml"
ARTICLES_URL = "/api/knowledge/v1/articulos/"


def article_url(pk) -> str:
    return f"{ARTICLES_URL}{pk}/"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture(scope="session")
def contract():
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def assert_contract_schema(contract):
    """Valida un cuerpo de respuesta contra un esquema de ``components`` del contrato."""

    def check(body, schema_name):
        schema = {
            "$ref": f"#/components/schemas/{schema_name}",
            "components": contract["components"],
        }
        OAS30ReadValidator(schema, format_checker=oas30_format_checker).validate(body)

    return check
