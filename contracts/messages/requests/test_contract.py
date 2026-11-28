
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parent


class RequestContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        envelope = json.loads(
            (ROOT.parent / "event-envelope.json").read_text(encoding="utf-8")
        )
        schema = json.loads(
            (ROOT / "event-routed.requests.v1.schema.json").read_text(
                encoding="utf-8"
            )
        )

        Draft202012Validator.check_schema(envelope)
        Draft202012Validator.check_schema(schema)

        registry = Registry().with_resource(
            envelope["$id"], Resource.from_contents(envelope)
        )

        cls.validator = Draft202012Validator(
            schema,
            registry=registry,
            format_checker=FormatChecker(),
        )

        cls.example = json.loads(
            (ROOT / "examples/catalog-request.json").read_text(
                encoding="utf-8"
            )
        )

    def test_valid_catalog_request(self):
        self.validator.validate(self.example)

    def test_valid_change_request(self):
        message = copy.deepcopy(self.example)
        message["payload"]["rule_code"] = "R8"
        message["payload"]["category"] = "CHANGE"

        self.validator.validate(message)

    def test_invalid_destination(self):
        message = copy.deepcopy(self.example)
        message["payload"]["destination"] = "INCIDENTS"

        self.assertFalse(self.validator.is_valid(message))

    def test_invalid_rule(self):
        message = copy.deepcopy(self.example)
        message["payload"]["rule_code"] = "R9"

        self.assertFalse(self.validator.is_valid(message))

    def test_invalid_category(self):
        message = copy.deepcopy(self.example)
        message["payload"]["category"] = "CHANGE"

        self.assertFalse(self.validator.is_valid(message))

    def test_missing_message_id(self):
        message = copy.deepcopy(self.example)
        del message["id"]

        self.assertFalse(self.validator.is_valid(message))

    def test_invalid_origin(self):
        message = copy.deepcopy(self.example)
        message["origin"] = "requests"

        self.assertFalse(self.validator.is_valid(message))

    def test_extra_payload_field(self):
        message = copy.deepcopy(self.example)
        message["payload"]["unexpected"] = True

        self.assertFalse(self.validator.is_valid(message))


if __name__ == "__main__":
    unittest.main()
