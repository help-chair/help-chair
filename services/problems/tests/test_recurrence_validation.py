"""Fronteras del adaptador local frente al perfil offline propuesto #36."""

import importlib.util
from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from recurrence.validation import ObservationError, aware_utc, reference, utc_timestamp, validate

CONTRACT = Path(__file__).resolve().parents[3] / "contracts/messages/incidents-problems"
SPEC = importlib.util.spec_from_file_location("observation_contract", CONTRACT / "validate.py")
offline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(offline)


@pytest.fixture
def message():
    return offline.load(CONTRACT / "examples/observed.json")


def change(message, field, value):
    target = message["payload"] if field.startswith("payload.") else message
    target[field.rsplit(".", 1)[-1]] = value


@pytest.mark.parametrize("version", [1, 1.0])
def test_canonical_example_and_optional_fields(message, version):
    message["version"] = version
    for correlation in (None, "00000000-0000-4000-8000-000000000038", "absent"):
        if correlation == "absent":
            message.pop("correlation_id")
        else:
            message["correlation_id"] = correlation
        before = deepcopy(message)
        payload, occurred, published = validate(message)
        assert payload == message["payload"]
        assert occurred.tzinfo == UTC and published >= occurred
        assert message == before
        assert offline.validate(message) == []
    message["payload"].pop("source_event_id")
    assert validate(message)[0] == message["payload"]
    assert offline.validate(message) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("type", "event.routed"),
        ("origin", "events"),
        ("version", True),
        ("version", False),
        ("version", "1"),
        ("version", 2),
        ("id", 38),
        ("id", "not-a-uuid"),
        ("id", "AAAAAAAA-0000-4000-8000-000000000038"),
        ("id", "00000000000040008000000000000038"),
        ("correlation_id", "bad"),
        ("correlation_id", 38),
        ("payload", []),
        ("payload", None),
        ("payload.company_ref", ""),
        ("payload.company_ref", None),
        ("payload.company_ref", "a b"),
        ("payload.company_ref", "a" * 65),
        ("payload.company_ref", " a"),
        ("payload.source_event_id", ""),
        ("payload.source_event_id", None),
        ("payload.source_event_id", "a\tb"),
        ("payload.source_event_id", "a" * 65),
        ("payload.incident_ref", "0"),
        ("payload.incident_ref", "01"),
        ("payload.incident_ref", "-1"),
        ("payload.incident_ref", 1),
        ("payload.incident_ref", "١"),
        ("payload.incident_ref", "1.0"),
        ("payload.incident_ref", str(2**63)),
        ("payload.affected_service", ""),
        ("payload.affected_service", None),
        ("payload.affected_service", " service"),
        ("payload.affected_service", "service "),
        ("payload.affected_service", "a\nb"),
        ("payload.affected_service", "a" * 101),
        ("timestamp", ""),
        ("timestamp", None),
        ("timestamp", "2026-11-24T12:00:01+00:00"),
        ("timestamp", "2026-11-24T12:00:01z"),
        ("timestamp", "2026-11-24T12:00:01.1234567Z"),
        ("timestamp", "2026-02-30T12:00:01Z"),
        ("timestamp", "2026-11-24T12:00:60Z"),
        ("timestamp", "2026-11-24T11:59:59Z"),
        ("occurred_at", "2026-11-24T12:00:01Z"),
        ("payload.created_at", "2026-11-24T12:00:01Z"),
    ],
)
def test_rejects_contract_negatives_without_mutation(message, field, value):
    change(message, field, value)
    before = deepcopy(message)
    with pytest.raises(ObservationError):
        validate(message)
    assert offline.validate(message)
    assert message == before


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "type",
        "version",
        "origin",
        "timestamp",
        "occurred_at",
        "payload",
        "payload.company_ref",
        "payload.incident_ref",
        "payload.created_at",
        "payload.affected_service",
    ],
)
def test_required_fields(message, field):
    target = message["payload"] if field.startswith("payload.") else message
    target.pop(field.rsplit(".", 1)[-1])
    with pytest.raises(ObservationError):
        validate(message)
    assert offline.validate(message)


@pytest.mark.parametrize("payload", [False, True])
def test_unknown_keys_and_private_diagnostics(message, payload):
    marker = "private-synthetic-marker"
    target = message["payload"] if payload else message
    target[marker] = marker
    with pytest.raises(ObservationError) as caught:
        validate(message)
    assert str(caught.value) == ("invalid-payload" if payload else "invalid-envelope")
    assert marker not in str(caught.value)
    assert all(marker not in error for error in offline.validate(message))


@pytest.mark.parametrize("value", [None, [], "", "{}", 1, True])
def test_already_decoded_object_required(value):
    with pytest.raises(ObservationError, match="^invalid-envelope$"):
        validate(value)
    assert offline.validate(value)


@pytest.mark.parametrize("field", ["company_ref", "source_event_id", "affected_service"])
def test_postgresql_nul_guard_is_stricter_than_current_schema(message, field):
    message["payload"][field] = "private-synthetic\x00marker"
    assert offline.validate(message) == []
    before = deepcopy(message)
    with pytest.raises(ObservationError) as caught:
        validate(message)
    assert str(caught.value) in {"invalid-reference", "invalid-service"}
    assert "private-synthetic" not in str(caught.value)
    assert message == before


@pytest.mark.parametrize("fraction", ["", ".1", ".123456"])
def test_timestamp_precision_and_equal_publication(message, fraction):
    value = "2026-11-24T12:00:00" + fraction + "Z"
    message.update(timestamp=value, occurred_at=value)
    message["payload"]["created_at"] = value
    assert validate(message)[1:] == (utc_timestamp(value), utc_timestamp(value))
    assert offline.validate(message) == []


def test_boundaries_preserve_case_and_internal_service_spaces(message):
    message["payload"].update(
        company_ref="a" * 64,
        source_event_id="b" * 64,
        incident_ref=str(2**63 - 1),
        affected_service="A " + "b" * 98,
    )
    assert validate(message)[0] == message["payload"]
    assert offline.validate(message) == []


@pytest.mark.parametrize(
    "value",
    [
        None,
        "2026-11-24T12:00:00Z",
        datetime(2026, 11, 24),
        datetime(2026, 11, 24, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_received_time_helper_requires_explicit_aware_utc(value):
    with pytest.raises(ObservationError):
        aware_utc(value)


def test_helpers_do_not_infer_time_or_normalize_references():
    value = datetime(2026, 11, 24, tzinfo=UTC)
    assert aware_utc(value) is value
    assert reference("Company-A") == "Company-A"
    for invalid in (None, "", "a b", "a\x00b", "a" * 65):
        with pytest.raises(ObservationError, match="^invalid-reference$"):
            reference(invalid)
