"""Concurrencia: N registros simultáneos de la misma huella dejan un solo evento.

Necesita PostgreSQL (SQLite serializa las escrituras y no ejerce la carrera real).
Se ejecuta con:  DATABASE_URL=postgres://... uv run pytest tests/test_deduplication_concurrency.py
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections, connection

from events.models import Event, EventOccurrence
from events.services import register_event

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        connection.vendor != "postgresql", reason="la prueba concurrente requiere PostgreSQL"
    ),
]

DATA = {
    "origin": "SYSTEM",
    "event_type": "WARNING",
    "title": "Latencia alta",
    "message": "Timeout de 5003 ms conectando a 10.0.0.12:5432",
    "payload": {},
}


@pytest.mark.parametrize("workers", [8, 24])
def test_simultaneous_registrations_create_a_single_event(workers):
    barrier = threading.Barrier(workers)

    def register(index):
        try:
            barrier.wait(timeout=10)  # todos arrancan al mismo tiempo
            _, created = register_event(
                {
                    **DATA,
                    "message": f"Timeout de {5000 + index} ms conectando a 10.0.0.{index}:5432",
                }
            )
            return created
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(register, range(workers)))

    assert results.count(True) == 1  # solo una petición creó el evento
    assert Event.objects.count() == 1
    event = Event.objects.get()
    assert event.occurrence_count == workers  # ninguna ocurrencia se perdió
    assert EventOccurrence.objects.filter(event=event).count() == workers
