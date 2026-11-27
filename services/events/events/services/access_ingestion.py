"""Validación, idempotencia y registro de mensajes publicados por Accesos."""

import base64
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..models import (
    AccessLoginFailureGroup,
    Event,
    EventCategory,
    EventOrigin,
    EventType,
    ProcessedAccessMessage,
)
from .registration import register_event

logger = logging.getLogger(__name__)

LOGIN_SUCCESS = "access.login.exitoso"
LOGIN_FAILED = "access.login.fallido"
ACCOUNT_LOCKED = "access.cuenta.bloqueada"
PASSWORD_CHANGED = "access.password.cambiada"
ACCESS_MESSAGE_TYPES = {LOGIN_SUCCESS, LOGIN_FAILED, ACCOUNT_LOCKED, PASSWORD_CHANGED}

ENVELOPE_REQUIRED = {
    "id",
    "type",
    "version",
    "origin",
    "timestamp",
    "occurred_at",
    "payload",
}
ENVELOPE_ALLOWED = ENVELOPE_REQUIRED | {"correlation_id"}


class InvalidAccessMessage(ValueError):
    """El mensaje no cumple el sobre común o el catálogo de Accesos."""


@dataclass(frozen=True)
class AccessIngestionResult:
    event: Event | None
    created: bool
    duplicate: bool
    failure_count: int | None = None


def _date_time(value, field):
    if not isinstance(value, str):
        raise InvalidAccessMessage(f"{field} debe ser una fecha ISO 8601.")
    parsed = parse_datetime(value)
    if parsed is None or not timezone.is_aware(parsed):
        raise InvalidAccessMessage(f"{field} debe incluir zona horaria.")
    return parsed


def _required_string(payload, field, *, allow_empty=False):
    value = payload.get(field)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise InvalidAccessMessage(f"payload.{field} debe ser texto.")
    return value


def _validate_payload(message_type, payload):
    if not isinstance(payload, dict):
        raise InvalidAccessMessage("payload debe ser un objeto.")

    required_fields = {
        LOGIN_SUCCESS: ("usuario_id", "rol", "ip"),
        LOGIN_FAILED: ("identificador", "intentos", "ip"),
        ACCOUNT_LOCKED: ("usuario_id", "intentos", "desbloquea_en"),
        PASSWORD_CHANGED: ("usuario_id", "forzado"),
    }[message_type]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise InvalidAccessMessage(f"Faltan campos de payload: {', '.join(missing)}.")

    if message_type in (LOGIN_SUCCESS, ACCOUNT_LOCKED, PASSWORD_CHANGED):
        _required_string(payload, "usuario_id")
    if message_type == LOGIN_SUCCESS:
        _required_string(payload, "rol")
    if message_type == LOGIN_FAILED:
        _required_string(payload, "identificador")
    if message_type in (LOGIN_FAILED, ACCOUNT_LOCKED):
        attempts = payload["intentos"]
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
            raise InvalidAccessMessage("payload.intentos debe ser un entero positivo.")
    if message_type in (LOGIN_SUCCESS, LOGIN_FAILED):
        ip = payload["ip"]
        if ip is not None and not isinstance(ip, str):
            raise InvalidAccessMessage("payload.ip debe ser texto o null.")
    if message_type == ACCOUNT_LOCKED:
        unlocks_at = payload["desbloquea_en"]
        if unlocks_at is not None:
            _date_time(unlocks_at, "payload.desbloquea_en")
    if message_type == PASSWORD_CHANGED and not isinstance(payload["forzado"], bool):
        raise InvalidAccessMessage("payload.forzado debe ser booleano.")


def validate_access_envelope(envelope):
    """Valida la porción aplicable del sobre y los datos definidos por Accesos."""
    if not isinstance(envelope, dict):
        raise InvalidAccessMessage("El mensaje debe ser un objeto JSON.")
    missing = ENVELOPE_REQUIRED - envelope.keys()
    extra = envelope.keys() - ENVELOPE_ALLOWED
    if missing:
        raise InvalidAccessMessage(f"Faltan campos del sobre: {', '.join(sorted(missing))}.")
    if extra:
        raise InvalidAccessMessage(f"Campos desconocidos en el sobre: {', '.join(sorted(extra))}.")

    if not isinstance(envelope["id"], str):
        raise InvalidAccessMessage("id debe ser un UUID válido.")
    try:
        message_id = UUID(envelope["id"])
    except (TypeError, ValueError, AttributeError) as error:
        raise InvalidAccessMessage("id debe ser un UUID válido.") from error
    if type(envelope["version"]) is not int or envelope["version"] != 1:
        raise InvalidAccessMessage("version debe ser el entero 1.")
    if envelope["origin"] != "access":
        raise InvalidAccessMessage('origin debe ser "access".')
    message_type = envelope["type"]
    if not isinstance(message_type, str) or message_type not in ACCESS_MESSAGE_TYPES:
        raise InvalidAccessMessage(f"Tipo de evento de Accesos no soportado: {message_type!r}.")
    if "correlation_id" in envelope and envelope["correlation_id"] is not None:
        if not isinstance(envelope["correlation_id"], str):
            raise InvalidAccessMessage("correlation_id debe ser un UUID o null.")
        try:
            UUID(envelope["correlation_id"])
        except (TypeError, ValueError, AttributeError) as error:
            raise InvalidAccessMessage("correlation_id debe ser un UUID o null.") from error

    _date_time(envelope["timestamp"], "timestamp")
    occurred_at = _date_time(envelope["occurred_at"], "occurred_at")
    _validate_payload(message_type, envelope["payload"])
    return message_id, message_type, occurred_at, envelope["payload"]


def _login_group_key(identifier, ip):
    normalized = [identifier.strip().casefold(), (ip or "").strip().casefold()]
    material = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _group_token(group_key):
    raw_hash = bytes.fromhex(group_key)
    return base64.b32encode(raw_hash).decode("ascii").rstrip("=").lower()


def _event_data(message_type, payload, occurred_at, event_type, group_key=""):
    ip = payload.get("ip") or "desconocida"
    if message_type == LOGIN_SUCCESS:
        title = "Inicio de sesión exitoso"
        message = f"Usuario {payload['usuario_id']} inició sesión desde IP {ip}."
    elif message_type == LOGIN_FAILED:
        title = (
            "Intento fallido de inicio de sesión"
            if event_type == EventType.INFORMATION
            else "Umbral de intentos fallidos de inicio de sesión alcanzado"
        )
        message = (
            f"Identificador {payload['identificador']} desde IP {ip}. "
            f"Grupo de intentos {_group_token(group_key)}."
        )
    elif message_type == ACCOUNT_LOCKED:
        title = "Cuenta bloqueada por intentos fallidos"
        message = f"Cuenta {payload['usuario_id']} bloqueada tras {payload['intentos']} intentos."
    else:
        title = "Cambio de contraseña forzado" if payload["forzado"] else "Contraseña cambiada"
        message = f"Usuario {payload['usuario_id']} cambió su contraseña."

    return {
        "origin": EventOrigin.SYSTEM,
        "event_type": event_type,
        "category": EventCategory.SECURITY,
        "title": title,
        "message": message,
        "payload": payload,
        "occurred_at": occurred_at,
        "ingestion_key": "",
        "action_required": event_type != EventType.INFORMATION,
    }


@transaction.atomic
def process_access_message(envelope) -> AccessIngestionResult:
    """Registra un mensaje una sola vez; una redelivery no vuelve a contar como intento."""
    message_id, message_type, occurred_at, payload = validate_access_envelope(envelope)

    group_key = ""
    if message_type == LOGIN_FAILED:
        group_key = _login_group_key(payload["identificador"], payload["ip"])
    try:
        with transaction.atomic():
            processed = ProcessedAccessMessage.objects.create(
                id=message_id,
                message_type=message_type,
                login_group_key=group_key,
                occurred_at=occurred_at,
            )
    except IntegrityError:
        processed = (
            ProcessedAccessMessage.objects.select_related("event").filter(pk=message_id).first()
        )
        if processed is None:
            raise
        return AccessIngestionResult(event=processed.event, created=False, duplicate=True)

    failure_count = None
    security_exception = message_type == ACCOUNT_LOCKED or (
        message_type == PASSWORD_CHANGED and payload["forzado"]
    )
    # El contrato no define login forzado ni permisos indebidos; se agregan cuando Accesos
    # publique esos tipos. Mientras tanto se cubren cuenta bloqueada y contraseña forzada.
    if message_type == LOGIN_FAILED:
        threshold = settings.LOGIN_FAILED_THRESHOLD
        window_seconds = settings.LOGIN_FAILED_WINDOW_SECONDS
        if threshold < 1 or window_seconds < 1:
            raise ImproperlyConfigured(
                "LOGIN_FAILED_THRESHOLD y LOGIN_FAILED_WINDOW_SECONDS deben ser positivos."
            )

        AccessLoginFailureGroup.objects.get_or_create(key=group_key)
        AccessLoginFailureGroup.objects.select_for_update().get(pk=group_key)
        cutoff = occurred_at - timedelta(seconds=window_seconds)
        failure_count = ProcessedAccessMessage.objects.filter(
            message_type=LOGIN_FAILED,
            login_group_key=group_key,
            occurred_at__gte=cutoff,
            occurred_at__lte=occurred_at,
        ).count()
        event_type = EventType.WARNING if failure_count >= threshold else EventType.INFORMATION
    elif security_exception:
        event_type = EventType.EXCEPTION
    else:
        event_type = EventType.INFORMATION

    event_data = _event_data(message_type, payload, occurred_at, event_type, group_key)
    event_data["ingestion_key"] = str(message_id)
    event, created = register_event(
        event_data,
        actor_ref="access",
        security_exception=security_exception,
    )
    processed.event = event
    processed.save(update_fields=["event"])

    logger.info(
        "access_message_processed",
        extra={
            "message_id": str(message_id),
            "message_type": message_type,
            "event_id": str(event.id),
            "event_type": event.event_type,
            "failure_count": failure_count,
        },
    )
    return AccessIngestionResult(
        event=event,
        created=created,
        duplicate=False,
        failure_count=failure_count,
    )
