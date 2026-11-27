"""register_event: carrera entre dos registros simultáneos de la misma huella."""

import pytest

from events.models import Event, EventOccurrence
from events.services import register_event, registration

pytestmark = pytest.mark.django_db

DATA = {"origin": "SYSTEM", "title": "CPU alta", "message": "90 %", "payload": {"host": "a"}}


def test_insert_race_on_the_same_fingerprint_counts_as_one_more_occurrence(monkeypatch):
    original, created = register_event(DATA)
    assert created

    # Simula que la consulta no vio el evento abierto (otra petición lo creó a la vez):
    # el INSERT viola uq_event_open_fingerprint y debe contarse como una ocurrencia más.
    real_find = registration.find_open_event_by_fingerprint
    calls = {"n": 0}

    def find_open_event(fingerprint):
        calls["n"] += 1
        return None if calls["n"] == 1 else real_find(fingerprint)

    monkeypatch.setattr(registration, "find_open_event_by_fingerprint", find_open_event)
    again, created_again = register_event(DATA)

    assert created_again is False
    assert again.pk == original.pk
    assert again.occurrence_count == 2
    assert Event.objects.count() == 1
    assert EventOccurrence.objects.count() == 2
