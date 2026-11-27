"""Boundary, privacy and replay scenarios for the proposed exchange (offline)."""

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from validate import (
    ENVELOPE,
    ROOT,
    ContractError,
    delivery_relation,
    load,
    main,
    validate,
)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.message = load(ROOT / "examples/observed.json")

    def test_canonical_example_and_minimal_observation(self):
        self.assertEqual(validate(self.message), [])
        del self.message["correlation_id"]
        del self.message["payload"]["source_event_id"]
        self.assertEqual(validate(self.message), [])

    def test_profile_preserves_envelope(self):
        envelope = Draft202012Validator(load(ENVELOPE), format_checker=FormatChecker())
        envelope.validate(self.message)
        # event.routed remains valid for the shared envelope, not this profile.
        routed = load(ENVELOPE)["examples"][0]
        envelope.validate(routed)
        self.assertTrue(validate(routed))

    def test_each_required_field(self):
        for container, keys in (
            (
                (),
                (
                    "id",
                    "type",
                    "version",
                    "origin",
                    "timestamp",
                    "occurred_at",
                    "payload",
                ),
            ),
            (
                ("payload",),
                ("company_ref", "incident_ref", "created_at", "affected_service"),
            ),
        ):
            for key in keys:
                with self.subTest(key=key):
                    message = copy.deepcopy(self.message)
                    target = message[container[0]] if container else message
                    del target[key]
                    self.assertTrue(validate(message))

    def test_invalid_fields(self):
        cases = {
            "id": ["bad-uuid", "00000000-0000-4000-8000-00000000003A", 36, None],
            "correlation_id": ["bad-uuid", 36],
            "type": ["event.routed", "incident.updated", None],
            "version": [0, 2, "1", True, None],
            "origin": ["events", "problems", None],
            "timestamp": [
                "invalid",
                "2026-02-30T10:00:00Z",
                "2026-11-24",
                "2026-11-24T12:00:01+00:00",
            ],
            "occurred_at": [None, "2026-11-24T12:00:00"],
            "payload.company_ref": ["", " ", "a b", "x" * 65, "tenant\n", None],
            "payload.incident_ref": [
                42,
                "0",
                "-1",
                "0042",
                "INC-000042",
                "9223372036854775808",
                "9" * 20,
                "42\n",
            ],
            "payload.affected_service": ["", " ", "x" * 101, " service", None],
            "payload.source_event_id": ["", "x" * 65, None],
            "payload.created_at": [None, "2026-02-30T10:00:00Z"],
            "payload": [None, [], "not-an-object"],
        }
        for path, values in cases.items():
            for value in values:
                with self.subTest(path=path, value_type=type(value).__name__):
                    message = copy.deepcopy(self.message)
                    parts = path.split(".")
                    target = message[parts[0]] if len(parts) == 2 else message
                    target[parts[-1]] = value
                    self.assertTrue(validate(message))

    def test_limits_and_unknown_fields(self):
        self.message["payload"].update(
            incident_ref=str(2**63 - 1),
            company_ref="c" * 64,
            affected_service="s" * 100,
            source_event_id="e" * 64,
        )
        self.assertEqual(validate(self.message), [])
        for target in (self.message, self.message["payload"]):
            target["private-unknown-key"] = "private-value"
            diagnostics = validate(self.message)
            self.assertTrue(diagnostics)
            self.assertNotIn("private", str(diagnostics))
            del target["private-unknown-key"]

    def test_dates_are_instants_and_publication_cannot_precede_creation(self):
        self.message["occurred_at"] = "2026-11-24T12:00:00.000Z"
        self.assertEqual(validate(self.message), [])
        self.message["timestamp"] = "2026-11-24T11:59:59Z"
        self.assertEqual(validate(self.message), ["timestamp:before-occurred_at"])
        self.message["timestamp"] = "2026-11-24T12:00:01Z"
        self.message["payload"]["created_at"] = "2026-11-24T11:00:00Z"
        self.assertEqual(validate(self.message), ["occurred_at:must-equal-created_at"])

    def test_unsupported_dates_fail_without_exceptions_or_private_values(self):
        for value in (
            "2026-11-24T12:00:60Z",
            "2026-11-24T12:00:00.0000001Z",
            "2026-11-24T12:00:00Z\n",
            "2026-11-24t12:00:00Z",
        ):
            for field in ("timestamp", "occurred_at", "created_at"):
                message = copy.deepcopy(self.message)
                target = message["payload"] if field == "created_at" else message
                target[field] = value
                diagnostics = validate(message)
                self.assertTrue(diagnostics)
                self.assertNotIn(value, str(diagnostics))

    def test_retries_reobservations_distinct_incidents_and_conflicts(self):
        other = copy.deepcopy(self.message)
        self.assertEqual(delivery_relation(self.message, other), "duplicate-message")
        other["payload"]["company_ref"] = "otra-empresa-sintetica"
        self.assertEqual(delivery_relation(self.message, other), "different-incident")
        other = copy.deepcopy(self.message)
        other["payload"]["incident_ref"] = "43"
        self.assertEqual(delivery_relation(self.message, other), "message-conflict")
        other = copy.deepcopy(self.message)
        other["timestamp"] = "2026-11-25T12:00:00Z"
        self.assertEqual(delivery_relation(self.message, other), "message-conflict")
        other["id"] = "00000000-0000-4000-8000-000000000037"
        self.assertEqual(delivery_relation(self.message, other), "same-incident")
        other["payload"]["affected_service"] = "otro-servicio-sintetico"
        self.assertEqual(delivery_relation(self.message, other), "incident-conflict")
        for field, value in (
            ("incident_ref", "43"),
            ("company_ref", "otra-empresa-sintetica"),
        ):
            changed = copy.deepcopy(other)
            changed["payload"][field] = value
            self.assertEqual(
                delivery_relation(self.message, changed), "different-incident"
            )
        other["version"] = 2
        with self.assertRaises(ContractError):
            delivery_relation(self.message, other)

    def test_offline_resolution_and_untrusted_json_diagnostics(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            self.assertEqual(validate(self.message), [])
        for content in ('{"id":1,"id":2}', '{"private":NaN}', '{"private":'):
            with tempfile.TemporaryDirectory(prefix="hc36-test-") as directory:
                path = Path(directory) / "input.json"
                path.write_text(content, encoding="utf-8")
                output = io.StringIO()
                with (
                    patch("sys.argv", ["validate.py", str(path)]),
                    redirect_stdout(output),
                    redirect_stderr(output),
                ):
                    self.assertEqual(main(), 2)
                self.assertNotIn("private", output.getvalue())

    def test_valid_cli_and_invalid_cli(self):
        with tempfile.TemporaryDirectory(prefix="hc36-test-") as directory:
            path = Path(directory) / "message.json"
            for version, status in ((1, 0), (2, 1)):
                self.message["version"] = version
                path.write_text(json.dumps(self.message), encoding="utf-8")
                with (
                    patch("sys.argv", ["validate.py", str(path)]),
                    redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(main(), status)


if __name__ == "__main__":
    unittest.main()
