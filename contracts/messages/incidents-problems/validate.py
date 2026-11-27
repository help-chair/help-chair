"""Offline proposal validator: structure and stateless semantics, no authentication."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent
ENVELOPE = ROOT.parent / "event-envelope.json"
FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=ValueError)
def utc_datetime(value):
    """Validate this profile's UTC microsecond timestamps without optional extras."""
    if not isinstance(value, str):
        return True
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.[0-9]{1,6})?Z", value
    ):
        return False
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return True


class ContractError(ValueError):
    """Only fixed rule names and schema paths may be exposed."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("json:duplicate-key")
        result[key] = value
    return result


def reject_constant(value):
    raise ContractError("json:non-finite-number")


def load(path):
    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, ValueError):
        raise ContractError("json:unreadable-or-invalid") from None


def no_remote(uri):
    raise ContractError("schema:unregistered-reference")


def validator():
    envelope = load(ENVELOPE)
    schema = load(ROOT / "incident-observed.v1.schema.json")
    Draft202012Validator.check_schema(envelope)
    Draft202012Validator.check_schema(schema)
    registry = Registry(retrieve=no_remote).with_resource(
        envelope["$id"], Resource.from_contents(envelope)
    )
    return Draft202012Validator(schema, registry=registry, format_checker=FORMATS)


def validate(message):
    """Return fixed diagnostics; never include keys/values supplied in a message."""
    errors = list(validator().iter_errors(message))
    if errors:
        # Schema paths belong to the trusted schema; instance paths can be private.
        return sorted(
            {"schema:/" + "/".join(map(str, error.schema_path)) for error in errors}
        )
    payload = message["payload"]
    for key in ("company_ref", "incident_ref", "affected_service", "source_event_id"):
        if key in payload and payload[key] != payload[key].strip():
            return ["payload." + key + ":surrounding-whitespace"]
    if int(payload["incident_ref"]) > 2**63 - 1:
        return ["payload.incident_ref:int64-range"]
    created = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
    occurred = datetime.fromisoformat(message["occurred_at"].replace("Z", "+00:00"))
    published = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
    if occurred != created:
        return ["occurred_at:must-equal-created_at"]
    if published < occurred:
        return ["timestamp:before-occurred_at"]
    return []


def delivery_relation(previous, incoming):
    """Compare two validated observations, not a persistent consumer or counter."""
    if validate(previous) or validate(incoming):
        raise ContractError("comparison:invalid-message")
    before, after = previous["payload"], incoming["payload"]
    if before["company_ref"] != after["company_ref"]:
        return "different-incident"
    if previous["id"] == incoming["id"]:
        return "duplicate-message" if previous == incoming else "message-conflict"
    identity = ("company_ref", "incident_ref")
    if any(before[key] != after[key] for key in identity):
        return "different-incident"
    return "same-incident" if before == after else "incident-conflict"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(load(args.message))
        for error in errors:
            print("FAIL " + error)
        if not errors:
            print("PASS structure and stateless semantics; authentication not checked")
        return int(bool(errors))
    except Exception:
        print("FAIL input-or-schema; details suppressed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
