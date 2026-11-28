"""Registro transaccional y carreras reales PostgreSQL del aporte #38."""

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from queue import Queue
from threading import Barrier, Event
from time import monotonic
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import close_old_connections, connection, transaction

from recurrence.models import IncidentObservation, ProcessedObservation
from recurrence.observations import company_lock, ingest
from recurrence.validation import ObservationError

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)
CANONICAL = (
    Path(__file__).resolve().parents[3]
    / "contracts/messages/incidents-problems/examples/observed.json"
)


@pytest.fixture
def message():
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def receive(item, *, at=NOW, company=None, producer="incidents"):
    return ingest(
        item,
        company_ref=company or item["payload"]["company_ref"],
        producer=producer,
        received_at=at,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("before,after", [(1, 1.0), (1.0, 1)])
def test_replay_normalizes_version_without_mutation_or_writes(message, before, after):
    message["version"] = before
    assert receive(message) == "accepted"
    message["version"] = after
    replay = dict(reversed(list(message.items())))
    replay["payload"] = dict(reversed(list(message["payload"].items())))
    original = deepcopy(replay)
    with (
        patch.object(IncidentObservation.objects, "create") as observation,
        patch.object(ProcessedObservation.objects, "create") as mark,
    ):
        assert receive(replay, at=NOW + timedelta(hours=1)) == "duplicate-message"
        observation.assert_not_called()
        mark.assert_not_called()
    assert replay == original and type(replay["version"]) is type(after)
    assert IncidentObservation.objects.count() == ProcessedObservation.objects.count() == 1
    assert ProcessedObservation.objects.get().received_at == NOW


@pytest.mark.django_db
def test_new_message_same_incident_preserves_first_reception(message):
    assert receive(message) == "accepted"
    original = IncidentObservation.objects.values().get()
    message["id"] = str(uuid4())
    assert receive(message, at=NOW + timedelta(hours=1)) == "same-incident"
    assert IncidentObservation.objects.values().get() == original
    assert ProcessedObservation.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("new_id", [False, True])
def test_conflicts_preserve_all_rows_and_private_diagnostics(message, new_id):
    receive(message)
    observations = list(IncidentObservation.objects.values())
    marks = list(ProcessedObservation.objects.values())
    message["payload"]["affected_service"] = "private-synthetic-marker"
    if new_id:
        message["id"] = str(uuid4())
    with pytest.raises(ObservationError) as caught:
        receive(message)
    assert str(caught.value) == ("incident-conflict" if new_id else "message-conflict")
    assert "private-synthetic-marker" not in str(caught.value)
    assert list(IncidentObservation.objects.values()) == observations
    assert list(ProcessedObservation.objects.values()) == marks


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["company", "producer", "occurred", "published", "naive", "nul"])
def test_rejects_before_lock_or_write(message, kind):
    kwargs = {}
    expected = {
        "company": "company-mismatch",
        "producer": "producer-mismatch",
        "occurred": "future-observation",
        "published": "future-observation",
        "naive": "explicit-aware-time-required",
        "nul": "invalid-service",
    }[kind]
    if kind == "company":
        kwargs["company"] = "another-synthetic-company"
    elif kind == "producer":
        kwargs["producer"] = "events"
    elif kind in {"occurred", "published"}:
        future = (NOW + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        message["timestamp"] = future
        if kind == "occurred":
            message["occurred_at"] = message["payload"]["created_at"] = future
    elif kind == "naive":
        kwargs["at"] = NOW.replace(tzinfo=None)
    else:
        message["payload"]["affected_service"] = "private\x00marker"
    with patch("recurrence.observations.company_lock") as lock:
        with pytest.raises(ObservationError) as caught:
            receive(message, **kwargs)
        assert str(caught.value) == expected
        lock.assert_not_called()
    assert IncidentObservation.objects.count() == ProcessedObservation.objects.count() == 0


@pytest.mark.django_db
def test_legitimate_company_contexts_have_independent_identities(message):
    receive(message)
    other = deepcopy(message)
    other["payload"]["company_ref"] = "another-synthetic-company"
    assert receive(other) == "accepted"
    assert IncidentObservation.objects.count() == ProcessedObservation.objects.count() == 2
    for item in (message, other):
        company = item["payload"]["company_ref"]
        assert IncidentObservation.objects.filter(company_ref=company).count() == 1
        assert ProcessedObservation.objects.filter(company_ref=company).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("outer", [False, True])
def test_second_write_failure_and_outer_rollback_are_atomic(message, outer):
    with pytest.raises(RuntimeError):
        if outer:
            with transaction.atomic():
                assert receive(message) == "accepted"
                raise RuntimeError("synthetic-rollback")
        else:
            with patch.object(ProcessedObservation.objects, "create", side_effect=RuntimeError):
                receive(message)
    assert IncidentObservation.objects.count() == ProcessedObservation.objects.count() == 0


@pytest.mark.django_db
def test_postgresql_guard_before_cursor():
    assert connection.vendor == "postgresql"
    with (
        patch.object(connection, "vendor", "unsupported"),
        patch.object(connection, "cursor") as cursor,
    ):
        with pytest.raises(ObservationError, match="^postgresql-required$"):
            company_lock("synthetic-company")
        cursor.assert_not_called()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "kind", ["redelivery", "same-incident", "conflict", "distinct", "message-conflict"]
)
def test_concurrent_first_insert(message, kind):
    assert connection.vendor == "postgresql"
    second = deepcopy(message)
    if kind not in {"redelivery", "message-conflict"}:
        second["id"] = str(uuid4())
    if kind in {"conflict", "message-conflict"}:
        second["payload"]["affected_service"] = "another-synthetic-service"
    if kind == "distinct":
        second["payload"]["incident_ref"] = "43"
    barrier = Barrier(2)

    def worker(item):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return receive(item)
            except ObservationError as error:
                return str(error)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(worker, [message, second]))
    expected = {
        "redelivery": "duplicate-message",
        "same-incident": "same-incident",
        "conflict": "incident-conflict",
        "distinct": "accepted",
        "message-conflict": "message-conflict",
    }[kind]
    assert sorted(outcomes) == sorted(["accepted", expected])
    assert IncidentObservation.objects.count() == (2 if kind == "distinct" else 1)
    assert ProcessedObservation.objects.count() == (
        2 if kind in {"same-incident", "distinct"} else 1
    )


@pytest.mark.django_db(transaction=True)
def test_company_lock_waits_until_outer_commit(message):
    locked, release = Event(), Event()
    backend = Queue()
    second = deepcopy(message)
    second["id"], second["payload"]["incident_ref"] = str(uuid4()), "43"

    def writer():
        close_old_connections()
        try:
            with transaction.atomic():
                assert receive(message) == "accepted"
                locked.set()
                assert release.wait(timeout=10)
        finally:
            close_old_connections()

    def waiter():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend.put(cursor.fetchone()[0])
            return receive(second)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        writing = pool.submit(writer)
        waiting = None
        try:
            assert locked.wait(timeout=10)
            waiting = pool.submit(waiter)
            pid = backend.get(timeout=10)
            deadline = monotonic() + 5
            while monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_stat_clear_snapshot()")
                    cursor.execute(
                        "SELECT wait_event_type, wait_event FROM pg_stat_activity WHERE pid = %s",
                        [pid],
                    )
                    state = cursor.fetchone()
                if state == ("Lock", "advisory"):
                    break
                assert not waiting.done(), "waiter finished before outer commit"
                release.wait(timeout=0.01)
            else:
                pytest.fail("advisory lock wait not observed")
            assert not waiting.done()
            assert IncidentObservation.objects.count() == 0
        finally:
            release.set()
        writing.result(timeout=15)
        assert waiting.result(timeout=15) == "accepted"
    assert IncidentObservation.objects.count() == ProcessedObservation.objects.count() == 2
