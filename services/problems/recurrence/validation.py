"""Validación local del perfil propuesto #36; nunca autentica mensajes."""

import re
from datetime import datetime
from uuid import UUID


class ObservationError(ValueError):
    """Diagnóstico fijo sin datos de entrada ni errores del driver."""


def utc_timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z", value
    ):
        raise ObservationError("invalid-utc-timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ObservationError("invalid-utc-timestamp") from None


def aware_utc(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ObservationError("explicit-aware-time-required")
    if value.utcoffset().total_seconds() != 0:
        raise ObservationError("utc-required")
    return value


def reference(value):
    if not isinstance(value, str) or not re.fullmatch(r"\S{1,64}", value) or "\x00" in value:
        raise ObservationError("invalid-reference")
    return value


def _uuid(value):
    if not isinstance(value, str):
        raise ObservationError("invalid-message-identity")
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except ValueError:
        raise ObservationError("invalid-message-identity") from None


def validate(message):
    """Validación runtime stdlib del perfil cerrado; contrato original intacto."""
    required = {"id", "type", "version", "origin", "timestamp", "occurred_at", "payload"}
    if not isinstance(message, dict) or not required <= message.keys():
        raise ObservationError("invalid-envelope")
    if message.keys() - required - {"correlation_id"}:
        raise ObservationError("invalid-envelope")
    if (
        message["type"] != "incident.observed"
        or isinstance(message["version"], bool)
        or message["version"] != 1
        or message["origin"] != "incidents"
    ):
        raise ObservationError("unsupported-profile")
    _uuid(message["id"])
    if message.get("correlation_id") is not None:
        _uuid(message["correlation_id"])
    payload = message["payload"]
    keys = {"company_ref", "incident_ref", "created_at", "affected_service"}
    if not isinstance(payload, dict) or not keys <= payload.keys():
        raise ObservationError("invalid-payload")
    if payload.keys() - keys - {"source_event_id"}:
        raise ObservationError("invalid-payload")
    reference(payload["company_ref"])
    incident = payload["incident_ref"]
    if (
        not isinstance(incident, str)
        or not re.fullmatch(r"[1-9][0-9]{0,18}", incident)
        or int(incident) > 2**63 - 1
    ):
        raise ObservationError("invalid-incident-reference")
    service = payload["affected_service"]
    if (
        not isinstance(service, str)
        or not 1 <= len(service) <= 100
        or service != service.strip()
        or "\n" in service
        or not re.fullmatch(r"\S(?:.*\S)?", service)
        or "\x00" in service
    ):
        raise ObservationError("invalid-service")
    if "source_event_id" in payload:
        reference(payload["source_event_id"])
    occurred = utc_timestamp(message["occurred_at"])
    published = utc_timestamp(message["timestamp"])
    if utc_timestamp(payload["created_at"]) != occurred or published < occurred:
        raise ObservationError("inconsistent-timestamps")
    # PostgreSQL text no admite NUL: rechazar antes de abrir transacción.
    if any("\x00" in value for value in payload.values() if isinstance(value, str)):
        raise ObservationError("invalid-payload")
    return payload, occurred, published
