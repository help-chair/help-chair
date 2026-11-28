"""Registro local del perfil propuesto #36; contexto confiable obligatorio."""

import hashlib
import json

from django.db import connection, transaction

from recurrence.models import IncidentObservation, ProcessedObservation
from recurrence.validation import ObservationError, aware_utc, reference, validate


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()


def company_lock(company_ref):
    """Serializa ingesta y lectura por empresa en nuestra BD PostgreSQL."""
    if connection.vendor != "postgresql":
        raise ObservationError("postgresql-required")
    key = int.from_bytes(hashlib.sha256(company_ref.encode()).digest()[:8], "big", signed=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])


def ingest(message, *, company_ref, producer, received_at):
    """El llamador debe aportar contexto autenticado; offline solo operador confiable.

    Una excepción no confirma el mensaje. Un ACK futuro requiere commit de la
    transacción MÁS EXTERNA (on_commit si se anida); retornar de esta función no
    basta dentro de otro atomic. No implementamos transporte ni autenticación.
    """
    reference(company_ref)
    aware_utc(received_at)
    payload, occurred, published = validate(message)
    if producer != "incidents" or message["origin"] != producer:
        raise ObservationError("producer-mismatch")
    if payload["company_ref"] != company_ref:
        raise ObservationError("company-mismatch")
    if published > received_at or occurred > received_at:
        raise ObservationError("future-observation")
    # JSON Schema admite 1 y 1.0 como el mismo entero; no mutar la entrada.
    message_digest = digest({**message, "version": 1})
    payload_digest = digest(payload)
    with transaction.atomic():
        company_lock(company_ref)
        mark = ProcessedObservation.objects.filter(
            company_ref=company_ref, producer=producer, message_id=message["id"]
        ).first()
        if mark:
            if mark.message_digest != message_digest:
                raise ObservationError("message-conflict")
            return "duplicate-message"
        previous = IncidentObservation.objects.filter(
            company_ref=company_ref, incident_ref=payload["incident_ref"]
        ).first()
        if previous and previous.payload_digest != payload_digest:
            raise ObservationError("incident-conflict")
        if not previous:
            IncidentObservation.objects.create(
                company_ref=company_ref,
                incident_ref=payload["incident_ref"],
                affected_service=payload["affected_service"],
                occurred_at=occurred,
                received_at=received_at,
                payload_digest=payload_digest,
            )
        ProcessedObservation.objects.create(
            company_ref=company_ref,
            producer=producer,
            message_id=message["id"],
            message_digest=message_digest,
            received_at=received_at,
        )
    return "same-incident" if previous else "accepted"
