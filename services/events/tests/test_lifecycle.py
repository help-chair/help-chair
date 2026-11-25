"""Ciclo de vida: transiciones, historial, asignación y cierre automático (regla 1)."""

import pytest

from events.models import (
    ActorType,
    ChangeType,
    ClosureCode,
    EventOrigin,
    EventState,
    EventType,
)
from events.services.lifecycle import (
    EventConflict,
    InvalidTransition,
    TransitionValidationError,
    allowed_transitions,
    assign_event,
    auto_close_informational,
    transition_event,
)
from tests.factories import make_event

pytestmark = pytest.mark.django_db


# --- transiciones ---------------------------------------------------------------------
def test_valid_transition_updates_state_and_records_who_and_when():
    event = make_event()
    event = transition_event(event, EventState.ASSIGNED, actor_ref="user-1")

    assert event.state == EventState.ASSIGNED
    entry = event.history.get()
    assert entry.change_type == ChangeType.STATE_CHANGE
    assert entry.actor_type == ActorType.USER
    assert entry.actor_ref == "user-1"
    assert (entry.from_state, entry.to_state) == (EventState.NEW, EventState.ASSIGNED)
    assert entry.changed_at is not None


def test_invalid_transition_raises_conflict_and_changes_nothing():
    event = make_event(state=EventState.CLOSED)
    with pytest.raises(InvalidTransition) as exc:
        transition_event(event, EventState.IN_PROGRESS)

    assert str(exc.value) == "No se puede pasar de CLOSED a IN_PROGRESS"
    assert exc.value.code == "invalid_transition"
    event.refresh_from_db()
    assert event.state == EventState.CLOSED
    assert event.history.count() == 0


def test_unknown_state_is_a_validation_error():
    with pytest.raises(TransitionValidationError) as exc:
        transition_event(make_event(), "NOPE")
    assert "to_state" in exc.value.fields


@pytest.mark.parametrize(
    "start, target",
    [(EventState.NEW, EventState.REJECTED), (EventState.ASSIGNED, EventState.CANCELLED)],
)
def test_reject_and_cancel_require_a_reason(start, target):
    event = make_event(state=start)
    with pytest.raises(TransitionValidationError) as exc:
        transition_event(event, target)
    assert "reason" in exc.value.fields

    event = transition_event(event, target, reason="  No procede  ")
    assert event.state_reason == "No procede"
    assert event.closed_at is not None
    assert event.closure_code == ClosureCode.NOT_APPLICABLE


def test_closure_code_only_applies_to_resolved_or_closed():
    with pytest.raises(TransitionValidationError) as exc:
        transition_event(make_event(), EventState.ASSIGNED, closure_code=ClosureCode.SOLVED)
    assert "closure_code" in exc.value.fields


def test_full_lifecycle_sets_dates_and_history():
    event = make_event()
    for state in (
        EventState.ASSIGNED,
        EventState.IN_PROGRESS,
        EventState.ON_HOLD,
        EventState.IN_PROGRESS,
        EventState.RESOLVED,
    ):
        event = transition_event(event, state, actor_ref="agent")
    assert event.resolved_at is not None and event.closed_at is None

    event = transition_event(event, EventState.CLOSED, actor_ref="agent")
    assert event.closed_at is not None
    assert event.closure_code == ClosureCode.SOLVED
    assert event.history.count() == 6


def test_reopening_clears_resolution_and_closing_dates():
    event = make_event()
    for state in (
        EventState.ASSIGNED,
        EventState.IN_PROGRESS,
        EventState.RESOLVED,
        EventState.CLOSED,
    ):
        event = transition_event(event, state)
    event = transition_event(event, EventState.REOPENED)

    assert event.state == EventState.REOPENED
    assert event.resolved_at is None and event.closed_at is None
    assert event.closure_code == ""


def test_allowed_transitions_list():
    assert allowed_transitions(make_event()) == [
        EventState.ASSIGNED,
        EventState.CLOSED,
        EventState.REJECTED,
    ]
    assert allowed_transitions(make_event(state=EventState.REJECTED)) == []


# --- asignación -----------------------------------------------------------------------
def test_assigning_a_new_event_moves_it_to_assigned_and_logs_both_changes():
    event = assign_event(make_event(), assigned_to_ref="user-7", actor_ref="lead-1")

    assert event.state == EventState.ASSIGNED
    assert event.assigned_to_ref == "user-7"
    types = list(event.history.order_by("id").values_list("change_type", flat=True))
    assert types == [ChangeType.ASSIGNMENT, ChangeType.STATE_CHANGE]
    assignment = event.history.get(change_type=ChangeType.ASSIGNMENT)
    assert assignment.actor_ref == "lead-1"
    assert assignment.new_value["assigned_to_ref"] == "user-7"


def test_reassigning_an_event_in_progress_keeps_its_state():
    event = make_event(state=EventState.IN_PROGRESS, assigned_to_ref="user-1")
    event = assign_event(event, assigned_to_ref="user-2")
    assert event.state == EventState.IN_PROGRESS
    assert event.history.count() == 1


def test_assignment_needs_a_user_or_a_group():
    with pytest.raises(TransitionValidationError):
        assign_event(make_event(), assigned_to_ref="", assigned_group_ref="")


def test_closed_events_cannot_be_assigned():
    with pytest.raises(EventConflict):
        assign_event(make_event(state=EventState.CLOSED), assigned_to_ref="user-1")


# --- regla 1: cierre automático -------------------------------------------------------
def test_system_informational_event_without_action_is_closed_automatically():
    event = auto_close_informational(make_event(action_required=False))

    assert event.state == EventState.CLOSED
    assert event.closed_at is not None
    assert event.closure_code == ClosureCode.AUTO_LOGGED
    entry = event.history.get()
    assert entry.actor_type == ActorType.RULE
    assert entry.rule_code == "R1"


@pytest.mark.parametrize(
    "origin, event_type, action_required",
    [
        (EventOrigin.USER, EventType.INFORMATION, False),
        (EventOrigin.SYSTEM, EventType.INFORMATION, True),
        (EventOrigin.SYSTEM, EventType.WARNING, False),
        (EventOrigin.SYSTEM, EventType.EXCEPTION, False),
    ],
)
def test_other_events_are_not_closed_automatically(origin, event_type, action_required):
    event = auto_close_informational(
        make_event(origin=origin, event_type=event_type, action_required=action_required)
    )
    assert event.state == EventState.NEW
    assert event.closed_at is None
    assert event.history.count() == 0
