import json
import logging
from typing import Any

from django.db import IntegrityError, transaction

from .models import CatalogItem, ServiceRequest

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_NAME = "Atención automática de eventos"
SYSTEM_REQUESTER_ID = 0
TARGET_DESTINATION = "REQUESTS"


class InvalidEventError(ValueError):
    """El mensaje recibido desde el broker no cumple con el esquema oficial."""


def _parse_positive_int(value: Any, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise InvalidEventError(f"El campo '{field_name}' debe ser un entero válido.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidEventError(f"El campo '{field_name}' debe ser un entero válido.") from exc
    if parsed <= 0:
        raise InvalidEventError(f"El campo '{field_name}' debe ser mayor a cero.")
    return parsed


def _resolve_catalog_item(service_code: str | None) -> CatalogItem:
    if service_code:
        existing = CatalogItem.objects.filter(
            name__iexact=service_code.strip(), is_active=True
        ).first()
        if existing is not None:
            return existing

    service_item, _ = CatalogItem.objects.get_or_create(
        name=DEFAULT_SERVICE_NAME,
        defaults={
            "description": "Servicio base para peticiones generadas automáticamente por eventos.",
            "is_active": True,
        },
    )
    return service_item


def process_routed_event(envelope: dict[str, Any]) -> tuple[ServiceRequest | None, bool]:
    """Crea una ServiceRequest idempotente a partir del sobre oficial event-envelope.json.

    Retorna `(service_request, created)`. Si el evento está dirigido a otro servicio
    (`destination != "REQUESTS"`), retorna `(None, False)`. Garantiza unicidad ante
    concurrencia mediante `UniqueConstraint` en `event_id`.
    """
    if not isinstance(envelope, dict):
        raise InvalidEventError("El mensaje debe ser un objeto JSON.")

    envelope_type = str(envelope.get("type") or "").strip()
    if envelope_type != "event.routed":
        raise InvalidEventError(f"Tipo de sobre no soportado para Peticiones: '{envelope_type}'.")

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise InvalidEventError("El campo 'payload' es obligatorio y debe ser un objeto.")

    destination = str(payload.get("destination") or "").strip().upper()
    if destination and destination != TARGET_DESTINATION:
        logger.info(
            "Evento ignorado por destino distinto",
            extra={"destination": destination, "envelope_id": envelope.get("id")},
        )
        return None, False

    raw_event_id = payload.get("event_id") or envelope.get("id")
    if not raw_event_id or not isinstance(raw_event_id, str):
        raise InvalidEventError("Falta el identificador obligatorio 'payload.event_id'.")
    event_id = raw_event_id.strip()

    existing = ServiceRequest.objects.filter(event_id=event_id).first()
    if existing is not None:
        logger.info(
            "Evento duplicado omitido",
            extra={"event_id": event_id, "request_id": str(existing.id)},
        )
        return existing, False

    category = str(payload.get("category") or "REQUEST").strip().upper()
    if category == "CHANGE":
        request_type = ServiceRequest.RequestType.CHANGE
        approval_status = ServiceRequest.ApprovalStatus.PENDING
    else:
        request_type = ServiceRequest.RequestType.SERVICE
        approval_status = ServiceRequest.ApprovalStatus.NOT_REQUIRED

    raw_title = str(
        payload.get("title") or payload.get("message") or f"Evento automático: {event_id}"
    ).strip()
    title = raw_title[:150]

    description_parts = []
    if payload.get("message"):
        description_parts.append(str(payload["message"]).strip())
    raw_event_data = payload.get("payload")
    if isinstance(raw_event_data, dict) and raw_event_data:
        description_parts.append(
            f"Datos del evento ({envelope_type}): {json.dumps(raw_event_data, ensure_ascii=False)}"
        )
    description = "\n".join(description_parts)

    reporter_ref = payload.get("reporter_ref")
    requester_id = (
        _parse_positive_int(reporter_ref, "reporter_ref")
        if reporter_ref is not None
        else SYSTEM_REQUESTER_ID
    )

    service_code = payload.get("service_code")
    catalog_item = _resolve_catalog_item(str(service_code) if service_code else None)

    try:
        with transaction.atomic():
            service_request = ServiceRequest.objects.create(
                request_type=request_type,
                approval_status=approval_status,
                service=catalog_item,
                title=title,
                description=description,
                requester_id=requester_id,
                event_id=event_id,
            )
    except IntegrityError:
        existing = ServiceRequest.objects.get(event_id=event_id)
        logger.info(
            "Evento duplicado concurrente resuelto por restricción única",
            extra={"event_id": event_id, "request_id": str(existing.id)},
        )
        return existing, False

    logger.info(
        "Petición creada desde evento",
        extra={
            "event_id": event_id,
            "request_id": str(service_request.id),
            "request_type": request_type,
        },
    )
    return service_request, True
