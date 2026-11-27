"""Garantías SQL de la proyección; no prueba ingesta ni autenticación."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db import IntegrityError, connection, transaction

from recurrence.models import IncidentObservation, ProcessedObservation

pytestmark = pytest.mark.django_db
NOW = datetime(2026, 11, 25, 12, 0, 0, 123456, tzinfo=UTC)


def observation(**overrides):
    values = {
        "company_ref": "empresa-sintetica-38",
        "incident_ref": "9223372036854775807",
        "affected_service": "servicio-sintetico",
        "occurred_at": NOW,
        "received_at": NOW,
        "payload_digest": "a" * 64,
    }
    return IncidentObservation.objects.create(**(values | overrides))


def mark(**overrides):
    values = {
        "company_ref": "empresa-sintetica-38",
        "producer": "productor-sintetico",
        "message_id": uuid4(),
        "message_digest": "b" * 64,
        "received_at": NOW,
    }
    return ProcessedObservation.objects.create(**(values | overrides))


def test_observation_unique_identity_preserves_original():
    assert connection.vendor == "postgresql"
    first = observation()
    with pytest.raises(IntegrityError), transaction.atomic():
        observation(affected_service="otro-servicio", payload_digest="c" * 64)
    first.refresh_from_db()
    assert first.affected_service == "servicio-sintetico"
    assert first.payload_digest == "a" * 64
    assert IncidentObservation.objects.count() == 1


def test_observation_identity_is_scoped_by_company():
    first = observation()
    other = observation(company_ref="otra-empresa-sintetica")
    assert first.incident_ref == other.incident_ref
    assert first.pk != other.pk
    assert IncidentObservation.objects.count() == 2


def test_mark_unique_identity_preserves_original():
    first = mark()
    with pytest.raises(IntegrityError), transaction.atomic():
        mark(message_id=first.message_id, message_digest="c" * 64)
    first.refresh_from_db()
    assert first.message_digest == "b" * 64
    assert ProcessedObservation.objects.count() == 1


@pytest.mark.parametrize(
    "changed", [{"company_ref": "otra-empresa-sintetica"}, {"producer": "otro-productor"}]
)
def test_message_identity_is_scoped_by_company_and_producer(changed):
    first = mark()
    other = mark(message_id=first.message_id, **changed)
    assert first.message_id == other.message_id
    assert first.pk != other.pk
    assert ProcessedObservation.objects.count() == 2


def test_distinct_message_identities_can_reference_the_same_observation():
    observation()
    first, second = mark(), mark()
    assert first.message_id != second.message_id
    assert IncidentObservation.objects.count() == 1
    assert ProcessedObservation.objects.count() == 2


def test_explicit_utc_timestamps_and_digests_round_trip():
    item, delivery = observation(), mark()
    item.refresh_from_db()
    delivery.refresh_from_db()
    assert item.occurred_at == item.received_at == delivery.received_at == NOW
    assert item.occurred_at.utcoffset().total_seconds() == 0
    assert item.payload_digest == "a" * 64
    assert delivery.message_digest == "b" * 64
    assert item.incident_ref == "9223372036854775807"


def test_outer_transaction_rolls_back_both_tables():
    with pytest.raises(RuntimeError, match="rollback"), transaction.atomic():
        observation()
        mark()
        raise RuntimeError("rollback")
    assert IncidentObservation.objects.count() == 0
    assert ProcessedObservation.objects.count() == 0


def test_text_representations_only_include_local_keys():
    item, delivery = observation(), mark()
    assert str(item) == f"Observation {item.pk}"
    assert str(delivery) == f"Processed observation {delivery.pk}"
