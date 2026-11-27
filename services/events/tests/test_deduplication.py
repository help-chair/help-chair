"""Deduplicación de eventos: huella exacta, duplicados parciales, similitud opcional y conteo."""

from datetime import timedelta

import pytest
from django.utils import timezone

from events.models import (
    BusinessService,
    ChangeType,
    Event,
    EventOccurrence,
    EventSource,
    EventState,
    MatchKind,
    RecurrencePolicy,
)
from events.services import register_event, similar_event_count

pytestmark = pytest.mark.django_db


def data(**overrides):
    base = {
        "origin": "SYSTEM",
        "event_type": "WARNING",
        "title": "Latencia alta",
        "message": "Timeout de 5003 ms conectando a 10.0.0.12:5432",
        "payload": {},
    }
    base.update(overrides)
    return base


# --- Etapa 1: huella exacta ----------------------------------------------------------------
def test_partial_duplicates_become_a_single_event_with_a_counter():
    first, created = register_event(data())
    second, created_2 = register_event(
        data(message="Timeout de 4890 ms conectando a 10.0.0.99:5432")
    )
    third, created_3 = register_event(data(payload={"host": "x"}))  # el payload no cuenta

    assert (created, created_2, created_3) == (True, False, False)
    assert first.pk == second.pk == third.pk
    assert Event.objects.count() == 1
    event = Event.objects.get()
    assert event.occurrence_count == 3
    assert EventOccurrence.objects.filter(event=event).count() == 3
    kinds = list(event.occurrences.order_by("id").values_list("match_kind", flat=True))
    assert kinds == [MatchKind.NEW, MatchKind.EXACT, MatchKind.EXACT]


@pytest.mark.parametrize(
    "change",
    [
        {"event_type": "EXCEPTION"},
        {"origin": "USER"},
        {"title": "Disco lleno"},
        {"message": "Timeout de 5003 ms conectando a la réplica"},
    ],
)
def test_different_events_are_not_merged(change):
    register_event(data())
    _, created = register_event(data(**change))
    assert created
    assert Event.objects.count() == 2


def test_different_service_or_source_are_not_merged():
    pagos = BusinessService.objects.create(code="pagos", name="Pagos", importance="HIGH")
    correo = BusinessService.objects.create(code="correo", name="Correo", importance="LOW")
    nagios = EventSource.objects.create(name="nagios", kind="WEBHOOK")
    register_event(data(service=pagos))
    assert register_event(data(service=correo))[1]
    assert register_event(data(service=pagos, source=nagios))[1]
    assert not register_event(data(service=pagos))[1]


def test_a_closed_event_does_not_absorb_new_occurrences():
    first, _ = register_event(data())
    Event.objects.filter(pk=first.pk).update(state=EventState.CLOSED)
    second, created = register_event(data())
    assert created and second.pk != first.pk


def test_late_occurrences_keep_first_and_last_seen_consistent():
    now = timezone.now()
    register_event(data(occurred_at=now))
    event, _ = register_event(data(occurred_at=now - timedelta(hours=2)))
    assert event.first_seen_at == now - timedelta(hours=2)
    assert event.last_seen_at == now


# --- n_eventos_similares ---------------------------------------------------------------------
def test_similar_event_count_uses_the_window_and_counts_previous_closed_events():
    now = timezone.now()
    old = now - timedelta(days=30)
    first, _ = register_event(data(occurred_at=old))  # fuera de la ventana por defecto (7 días)
    Event.objects.filter(pk=first.pk).update(state=EventState.CLOSED)
    for hours in (3, 2):
        event, _ = register_event(data(occurred_at=now - timedelta(hours=hours)))
        Event.objects.filter(pk=event.pk).update(state=EventState.CLOSED)
    event, _ = register_event(data(occurred_at=now))

    assert similar_event_count(event) == 3  # 3 dentro de 7 días; la de hace 30 días no cuenta
    assert similar_event_count(event, window_days=60) == 4


def test_window_comes_from_the_recurrence_policy():
    RecurrencePolicy.objects.create(event_type="WARNING", threshold_count=2, window_days=1)
    now = timezone.now()
    register_event(data(occurred_at=now - timedelta(days=3)))
    event, _ = register_event(data(occurred_at=now))
    assert similar_event_count(event) == 1  # T = 1 día: la de hace 3 días queda fuera


def test_rule_3_alert_counts_occurrences_across_closed_events():
    """Un patrón repetido en cierres sucesivos también cruza el umbral."""
    for _ in range(2):
        event, _ = register_event(data())
        Event.objects.filter(pk=event.pk).update(state=EventState.CLOSED)
    event, _ = register_event(data())  # tercera ocurrencia en la ventana: umbral por defecto = 3
    alerts = event.history.filter(rule_code="R3")
    assert alerts.count() == 1


# --- Etapa 2: similitud (opcional) ---------------------------------------------------------
BASE_MSG = "no se puede conectar a la base de datos primary del cluster"


@pytest.fixture
def fuzzy(settings):
    settings.EVENT_FUZZY_ENABLED = True


def test_fuzzy_is_disabled_by_default():
    register_event(data(message=BASE_MSG))
    _, created = register_event(data(message=BASE_MSG.replace("primary", "primay")))
    assert created  # sin la bandera, una errata es otro evento


def test_fuzzy_merges_typos_and_records_why(fuzzy):
    first, _ = register_event(data(message=BASE_MSG))
    merged, created = register_event(data(message=BASE_MSG.replace("primary", "primay")))

    assert not created and merged.pk == first.pk
    occurrence = merged.occurrences.get(match_kind=MatchKind.FUZZY)
    assert 0.95 <= occurrence.similarity < 1.0
    assert occurrence.fingerprint == first.fingerprint  # cuenta para n_eventos_similares
    entry = merged.history.get(change_type=ChangeType.SYSTEM, actor_ref="dedup")
    assert "similitud" in entry.description


@pytest.mark.parametrize(
    "other",
    [
        BASE_MSG.replace("primary", "replica"),  # otra palabra
        BASE_MSG + " ahora mismo",  # palabras de más
        "no se puede conectar a la base de datos primary del cluster 500",
    ],
)
def test_fuzzy_does_not_over_merge(fuzzy, other):
    register_event(data(message=BASE_MSG))
    _, created = register_event(data(message=other))
    assert created


def test_fuzzy_does_not_merge_status_codes(fuzzy):
    msg = "la solicitud falló con el código de estado {} en el servidor"
    register_event(data(message=msg.format(500)))
    assert register_event(data(message=msg.format(404)))[1]


def test_fuzzy_never_applies_to_security_or_other_types(fuzzy):
    typo = BASE_MSG.replace("primary", "primay")
    register_event(data(message=BASE_MSG, category="SECURITY"))
    assert register_event(data(message=typo, category="SECURITY"))[1]
    register_event(data(message=BASE_MSG, event_type="EXCEPTION"))
    assert register_event(data(message=typo, event_type="EXCEPTION"))[1]


def test_fuzzy_requires_same_service_and_origin(fuzzy):
    pagos = BusinessService.objects.create(code="pagos", name="Pagos", importance="HIGH")
    typo = BASE_MSG.replace("primary", "primay")
    register_event(data(message=BASE_MSG, service=pagos))
    assert register_event(data(message=typo))[1]  # sin servicio
    assert register_event(data(message=typo, service=pagos, origin="USER"))[1]


def test_fuzzy_ignores_events_outside_the_window(fuzzy):
    now = timezone.now()
    register_event(data(message=BASE_MSG, occurred_at=now - timedelta(days=30)))
    _, created = register_event(
        data(message=BASE_MSG.replace("primary", "primay"), occurred_at=now)
    )
    assert created
