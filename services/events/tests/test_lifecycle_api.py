"""API del ciclo de vida: transiciones, asignación, historial, reglas 1 y 3 y formato de errores."""

import pytest
from rest_framework.test import APIClient

from events.models import (
    BusinessService,
    EventState,
    PriorityMatrix,
    RecurrencePolicy,
    SlaPolicy,
)
from tests.factories import make_event

pytestmark = pytest.mark.django_db

ACTOR = {"HTTP_X_ACTOR_REF": "user-42"}


@pytest.fixture
def api(settings):
    settings.ALLOW_ACTOR_HEADER = True  # identifica al actor con X-Actor-Ref (solo pruebas)
    return APIClient()


def post_event(api, **overrides):
    body = {"origin": "SYSTEM", "title": "Disco lleno", "message": "95 % usado", "payload": {}}
    body.update(overrides)
    return api.post("/api/v1/events", body, format="json")


# --- transiciones -----------------------------------------------------------------------
def test_valid_transition_returns_the_event_and_records_who(api):
    event = make_event()
    response = api.post(
        f"/api/v1/events/{event.id}/transitions", {"to_state": "ASSIGNED"}, format="json", **ACTOR
    )

    assert response.status_code == 200
    assert response.json()["state"] == "ASSIGNED"
    history = api.get(f"/api/v1/events/{event.id}/history").json()
    assert history["count"] == 1
    entry = history["results"][0]
    assert entry["change_type"] == "STATE_CHANGE"
    assert entry["actor_type"] == "USER"
    assert entry["actor_ref"] == "user-42"
    assert (entry["from_state"], entry["to_state"]) == ("NEW", "ASSIGNED")
    assert entry["changed_at"]


def test_invalid_transition_returns_409_with_the_contract_error(api):
    event = make_event(state=EventState.CLOSED)
    response = api.post(
        f"/api/v1/events/{event.id}/transitions", {"to_state": "IN_PROGRESS"}, format="json"
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "invalid_transition",
        "detail": "No se puede pasar de CLOSED a IN_PROGRESS",
    }
    assert api.get(f"/api/v1/events/{event.id}/history").json()["count"] == 0


def test_rejecting_without_a_reason_returns_422(api):
    event = make_event()
    response = api.post(
        f"/api/v1/events/{event.id}/transitions", {"to_state": "REJECTED"}, format="json"
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert "reason" in body["fields"]

    ok = api.post(
        f"/api/v1/events/{event.id}/transitions",
        {"to_state": "REJECTED", "reason": "No procede"},
        format="json",
    )
    assert ok.status_code == 200
    assert ok.json()["state_reason"] == "No procede"
    assert ok.json()["closed_at"] is not None


def test_unknown_state_returns_422(api):
    event = make_event()
    response = api.post(
        f"/api/v1/events/{event.id}/transitions", {"to_state": "NOPE"}, format="json"
    )
    assert response.status_code == 422
    assert "to_state" in response.json()["fields"]


def test_allowed_transitions_endpoint(api):
    event = make_event()
    response = api.get(f"/api/v1/events/{event.id}/transitions")
    assert response.status_code == 200
    assert response.json() == {"state": "NEW", "allowed": ["ASSIGNED", "CLOSED", "REJECTED"]}


@pytest.mark.parametrize(
    "method, suffix", [("get", ""), ("get", "/transitions"), ("get", "/history")]
)
def test_unknown_event_returns_404_with_the_contract_error(api, method, suffix):
    response = getattr(api, method)(f"/api/v1/events/00000000-0000-0000-0000-000000000000{suffix}")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert "detail" in response.json()


def test_method_not_allowed_also_uses_the_error_format(api):
    response = api.delete("/api/v1/events")
    assert response.status_code == 405
    assert response.json()["code"] == "method_not_allowed"


# --- asignación (PATCH) -------------------------------------------------------------------
def test_assigning_a_new_event_sets_assigned_and_logs_it(api):
    event = make_event()
    response = api.patch(
        f"/api/v1/events/{event.id}", {"assigned_to_ref": "user-7"}, format="json", **ACTOR
    )

    assert response.status_code == 200
    assert response.json()["state"] == "ASSIGNED"
    assert response.json()["assigned_to_ref"] == "user-7"
    entries = api.get(f"/api/v1/events/{event.id}/history").json()["results"]
    assert [e["change_type"] for e in entries] == [
        "STATE_CHANGE",
        "ASSIGNMENT",
    ]  # más reciente primero
    assert {e["actor_ref"] for e in entries} == {"user-42"}


def test_patch_with_no_fields_returns_422(api):
    response = api.patch(f"/api/v1/events/{make_event().id}", {}, format="json")
    assert response.status_code == 422


def test_patch_on_a_closed_event_returns_409(api):
    event = make_event(state=EventState.CLOSED)
    response = api.patch(f"/api/v1/events/{event.id}", {"assigned_to_ref": "u"}, format="json")
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_clearing_the_only_assignee_is_rejected(api):
    event = make_event(state=EventState.IN_PROGRESS, assigned_to_ref="user-1")
    response = api.patch(f"/api/v1/events/{event.id}", {"assigned_to_ref": None}, format="json")
    assert response.status_code == 422


def test_reclassifying_recalculates_priority_and_sla(api):
    PriorityMatrix.objects.create(impact="HIGH", urgency="HIGH", priority="P1")
    SlaPolicy.objects.create(priority="P1", response_minutes=15, resolution_minutes=60)
    event = make_event()

    response = api.patch(
        f"/api/v1/events/{event.id}",
        {"impact": "HIGH", "urgency": "HIGH", "note": "Afecta a todos los clientes"},
        format="json",
        **ACTOR,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == "P1"
    assert body["response_due_at"] is not None
    types = {
        e["change_type"] for e in api.get(f"/api/v1/events/{event.id}/history").json()["results"]
    }
    assert types == {"CLASSIFICATION", "PRIORITY_CHANGE", "NOTE"}


# --- historial ----------------------------------------------------------------------------
def test_history_uses_null_for_empty_values_and_paginates(api):
    event = make_event()
    for state in ("ASSIGNED", "IN_PROGRESS"):
        api.post(f"/api/v1/events/{event.id}/transitions", {"to_state": state}, format="json")

    page = api.get(f"/api/v1/events/{event.id}/history", {"limit": 1}).json()
    assert page["count"] == 2
    assert len(page["results"]) == 1
    assert page["next"] is not None
    entry = page["results"][0]
    assert entry["to_state"] == "IN_PROGRESS"  # más reciente primero
    assert entry["actor_ref"] is None and entry["rule_code"] is None


# --- regla 1: cierre automático -------------------------------------------------------------
def test_system_informational_event_without_action_is_closed_on_registration(api):
    response = post_event(api, event_type="INFORMATION", action_required=False, title="Backup ok")

    assert response.status_code == 201
    body = response.json()
    assert body["state"] == "CLOSED"
    assert body["closure_code"] == "AUTO_LOGGED"
    assert body["closed_at"] is not None
    entries = api.get(f"/api/v1/events/{body['id']}/history").json()["results"]
    assert entries[0]["actor_type"] == "RULE" and entries[0]["rule_code"] == "R1"


@pytest.mark.parametrize(
    "extra",
    [
        {"origin": "USER", "event_type": "INFORMATION", "action_required": False},
        {"event_type": "INFORMATION", "action_required": True},
        {"event_type": "WARNING", "action_required": False},
    ],
)
def test_other_events_stay_open_on_registration(api, extra):
    assert post_event(api, **extra).json()["state"] == "NEW"


# --- clasificación y regla 3 ----------------------------------------------------------------
@pytest.mark.parametrize(
    "extra, expected",
    [
        ({"event_type": "INFORMATION"}, "INFORMATION"),
        ({"event_type": "WARNING"}, "WARNING"),
        ({"event_type": "EXCEPTION"}, "EXCEPTION"),
        ({"payload": {"severity": "error"}}, "EXCEPTION"),
        ({"payload": {"severity": "info"}}, "INFORMATION"),
        ({"payload": {}}, "WARNING"),
        ({"origin": "USER", "payload": {}}, "EXCEPTION"),
    ],
)
def test_event_type_is_classified_on_registration(api, extra, expected):
    assert post_event(api, **extra).json()["event_type"] == expected


def history(api, event_id):
    return api.get(f"/api/v1/events/{event_id}/history").json()["results"]


def test_warning_alert_is_raised_once_when_the_default_threshold_is_reached(api):
    body = {"event_type": "WARNING", "title": "CPU alta", "payload": {"host": "a"}}
    first = post_event(api, **body)
    event_id = first.json()["id"]
    assert first.status_code == 201
    assert post_event(api, **body).json()["occurrence_count"] == 2
    assert not [e for e in history(api, event_id) if e["rule_code"] == "R3"]  # bajo el umbral

    third = post_event(api, **body)
    assert third.status_code == 200 and third.json()["occurrence_count"] == 3
    alerts = [e for e in history(api, event_id) if e["rule_code"] == "R3"]
    assert len(alerts) == 1
    assert alerts[0]["metadata"]["threshold_count"] == 3

    post_event(api, **body)  # cuarta ocurrencia: no repite la alerta
    assert len([e for e in history(api, event_id) if e["rule_code"] == "R3"]) == 1


def test_threshold_is_configurable_with_a_recurrence_policy(api):
    service = BusinessService.objects.create(code="pagos", name="Pagos", importance="HIGH")
    RecurrencePolicy.objects.create(
        event_type="WARNING", service=service, threshold_count=2, window_days=7
    )
    body = {"event_type": "WARNING", "service_code": "pagos", "title": "Latencia"}
    event_id = post_event(api, **body).json()["id"]
    assert not [e for e in history(api, event_id) if e["rule_code"] == "R3"]

    post_event(api, **body)
    assert len([e for e in history(api, event_id) if e["rule_code"] == "R3"]) == 1


def test_actor_header_is_ignored_unless_enabled(settings):
    settings.ALLOW_ACTOR_HEADER = False
    api = APIClient()
    event = make_event()
    api.post(
        f"/api/v1/events/{event.id}/transitions", {"to_state": "ASSIGNED"}, format="json", **ACTOR
    )
    entry = history(api, event.id)[0]
    assert entry["actor_ref"] is None
