from pathlib import Path

import pytest
import schemathesis
from schemathesis.config import GenerationConfig
from schemathesis.generation import GenerationMode
from schemathesis.specs.openapi.checks import ignored_auth

from config.wsgi import application

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"
EVENTS_OPENAPI = CONTRACTS / "events" / "openapi.yaml"
schema = schemathesis.openapi.from_path(str(EVENTS_OPENAPI))
schema.app = application
schema.config.generation = GenerationConfig(
    modes=[GenerationMode.POSITIVE],
    max_examples=5,
    allow_x00=False,
    deterministic=True,
)


@schema.parametrize()
@pytest.mark.django_db(transaction=True)
def test_events_api_conforms_to_v1_contract(case):
    if isinstance(case.body, dict):
        # Optional foreign keys need pre-existing catalog rows, so use their absent values.
        case.body.pop("service_code", None)
        case.body.pop("source_name", None)

    # Gateway authentication is outside this in-process WSGI contract test.
    case.call_and_validate(
        base_url="http://testserver/api/v1",
        headers={
            "Authorization": "Bearer gateway-test-token",
            "X-API-Key": "gateway-test-api-key",
        },
        excluded_checks=[ignored_auth],
    )
