"""Clasificación por tipo y regla 3 (advertencia bajo el umbral: vigilancia y alerta)."""

import pytest

from events.models import (
    ActorType,
    BusinessService,
    ChangeType,
    EventCategory,
    EventOrigin,
    EventType,
    RecurrenceAction,
    RecurrencePolicy,
)
from events.services.classification import (
    classify_event_type,
    resolve_recurrence,
    watch_warning,
)
from tests.factories import make_event


# --- clasificación en los tres tipos -------------------------------------------------
@pytest.mark.parametrize(
    "declared", [EventType.INFORMATION, EventType.WARNING, EventType.EXCEPTION]
)
def test_declared_type_is_respected(declared):
    assert classify_event_type(origin=EventOrigin.SYSTEM, declared=declared) == declared


@pytest.mark.parametrize(
    "severity, expected",
    [
        ("info", EventType.INFORMATION),
        ("DEBUG", EventType.INFORMATION),
        ("warning", EventType.WARNING),
        (" warn ", EventType.WARNING),
        ("error", EventType.EXCEPTION),
        ("Critical", EventType.EXCEPTION),
    ],
)
def test_type_comes_from_payload_severity_when_not_declared(severity, expected):
    result = classify_event_type(origin=EventOrigin.SYSTEM, payload={"severity": severity})
    assert result == expected


@pytest.mark.parametrize(
    "origin, expected",
    [(EventOrigin.USER, EventType.EXCEPTION), (EventOrigin.SYSTEM, EventType.WARNING)],
)
def test_default_type_depends_on_origin(origin, expected):
    assert classify_event_type(origin=origin, payload={}) == expected


def test_invalid_declared_type_is_rejected():
    with pytest.raises(ValueError):
        classify_event_type(origin=EventOrigin.SYSTEM, declared="CRITICAL")


def test_severity_map_is_configurable(settings):
    settings.EVENT_SEVERITY_KEY = "level"
    settings.EVENT_SEVERITY_MAP = {"sev1": "EXCEPTION"}
    result = classify_event_type(origin=EventOrigin.SYSTEM, payload={"level": "sev1"})
    assert result == EventType.EXCEPTION


# --- umbral configurable ------------------------------------------------------------
@pytest.mark.django_db
class TestRecurrence:
    def test_default_threshold_when_there_is_no_policy(self):
        rec = resolve_recurrence(make_event(event_type=EventType.WARNING))
        assert (rec.threshold_count, rec.window_days, rec.source) == (3, 7, "default")

    def test_default_threshold_can_be_changed_in_settings(self, settings):
        settings.EVENT_RECURRENCE_DEFAULT = {"threshold_count": 10}
        rec = resolve_recurrence(make_event(event_type=EventType.WARNING))
        assert (rec.threshold_count, rec.window_days) == (10, 7)

    def test_policy_overrides_the_default(self):
        policy = RecurrencePolicy.objects.create(
            event_type=EventType.WARNING, threshold_count=5, window_days=10
        )
        rec = resolve_recurrence(make_event(event_type=EventType.WARNING))
        assert (rec.threshold_count, rec.window_days) == (5, 10)
        assert rec.source == f"policy:{policy.id}"

    def test_the_most_specific_policy_wins(self):
        service = BusinessService.objects.create(code="pagos", name="Pagos", importance="HIGH")
        RecurrencePolicy.objects.create(
            event_type=EventType.WARNING, threshold_count=5, window_days=7
        )
        RecurrencePolicy.objects.create(
            event_type=EventType.WARNING, service=service, threshold_count=2, window_days=1
        )
        general = make_event(event_type=EventType.WARNING)
        specific = make_event(event_type=EventType.WARNING, service=service)
        assert resolve_recurrence(general).threshold_count == 5
        assert resolve_recurrence(specific).threshold_count == 2

    def test_inactive_and_non_matching_policies_are_ignored(self):
        RecurrencePolicy.objects.create(
            event_type=EventType.WARNING, threshold_count=9, window_days=9, is_active=False
        )
        RecurrencePolicy.objects.create(
            event_type=EventType.EXCEPTION, threshold_count=8, window_days=8
        )
        RecurrencePolicy.objects.create(
            category=EventCategory.SECURITY, threshold_count=7, window_days=7
        )
        rec = resolve_recurrence(make_event(event_type=EventType.WARNING))
        assert rec.source == "default"

    def test_policy_action_is_returned(self):
        RecurrencePolicy.objects.create(
            event_type=EventType.WARNING,
            threshold_count=4,
            window_days=3,
            action=RecurrenceAction.CREATE_PROBLEM,
        )
        rec = resolve_recurrence(make_event(event_type=EventType.WARNING))
        assert rec.action == RecurrenceAction.CREATE_PROBLEM


# --- regla 3: vigilancia y alerta ---------------------------------------------------
@pytest.mark.django_db
class TestWarningWatch:
    def test_warning_below_the_threshold_is_only_watched(self):
        event = make_event(event_type=EventType.WARNING, occurrence_count=1)
        result = watch_warning(event, previous_count=0)
        assert result.watching and not result.threshold_exceeded and not result.alert_raised
        assert event.history.count() == 0

    def test_alert_is_raised_when_the_counter_reaches_the_threshold(self):
        event = make_event(event_type=EventType.WARNING, occurrence_count=3)
        result = watch_warning(event, previous_count=2)

        assert result.alert_raised and result.threshold_exceeded and not result.watching
        entry = event.history.get()
        assert entry.change_type == ChangeType.SYSTEM
        assert entry.actor_type == ActorType.RULE
        assert entry.rule_code == "R3"
        assert entry.metadata["threshold_count"] == 3

    def test_alert_is_raised_only_once(self):
        event = make_event(event_type=EventType.WARNING, occurrence_count=4)
        result = watch_warning(event, previous_count=3)
        assert result.threshold_exceeded and not result.alert_raised
        assert event.history.count() == 0

    def test_threshold_is_configurable_with_a_policy(self):
        RecurrencePolicy.objects.create(
            event_type=EventType.WARNING, threshold_count=2, window_days=7
        )
        event = make_event(event_type=EventType.WARNING, occurrence_count=2)
        assert watch_warning(event, previous_count=1).alert_raised

    @pytest.mark.parametrize("event_type", [EventType.INFORMATION, EventType.EXCEPTION])
    def test_only_warnings_are_watched(self, event_type):
        event = make_event(event_type=event_type, occurrence_count=9)
        assert watch_warning(event, previous_count=8) is None
        assert event.history.count() == 0
