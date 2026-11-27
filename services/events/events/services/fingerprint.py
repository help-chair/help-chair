"""Normalización del texto y huella de deduplicación.

Huella = tipo + origen + fuente + servicio + título normalizado + mensaje normalizado.
El `payload` NO entra: dos ocurrencias del mismo problema casi nunca traen el mismo payload.
"""

import hashlib
import json
import re
import unicodedata

from django.conf import settings

FINGERPRINT_VERSION = (
    "v2"  # súbela si cambia la normalización: las huellas anteriores dejan de coincidir
)

# Datos volátiles que cambian en cada ocurrencia, en orden de más a menos específico.
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
_TIMESTAMP = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[t ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:z|[+-]\d{2}:?\d{2})?"
)
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_TIME = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?\b")
_HEX = re.compile(r"\b0x[0-9a-f]+\b|\b[0-9a-f]{8,}\b")
_QUANTITY = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:(?:ms|s|seg|min|h|kb|mb|gb|tb|b)\b|%)")
_LONG_NUMBER = re.compile(r"\b\d{5,}\b")
_ANY_NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_SPACES = re.compile(r"\s+")

_MASKS = (
    (_UUID, "<uuid>"),
    (_TIMESTAMP, "<ts>"),
    (_DATE, "<date>"),
    (_TIME, "<time>"),
    (_IPV4, "<ip>"),
    (_HEX, "<hex>"),
    (_QUANTITY, "<qty>"),
    (_LONG_NUMBER, "<num>"),
)


def _normalize_payload(payload: dict | list | str | int | float | bool | None):
    """Normaliza valores dentro de payloads de forma recursiva y determinista."""
    if payload is None or isinstance(payload, bool | int | float):
        return payload
    if isinstance(payload, str):
        return normalize_text(payload)
    if isinstance(payload, dict):
        return {
            _as_text(k): _normalize_payload(v)
            for k, v in sorted(payload.items(), key=lambda item: _as_text(item[0]))
        }
    if isinstance(payload, list):
        return [_normalize_payload(item) for item in payload]
    return normalize_text(_as_text(payload))


def normalize_text(text: str, *, mask_short_numbers: bool | None = None) -> str:
    """Minúsculas, espacios colapsados y datos volátiles reemplazados por marcadores.

    Los números cortos (códigos HTTP, "intento 3") se conservan por defecto: fusionar
    "status 500" con "status 404" sería un *over-merge*. Actívalos con EVENT_MASK_SHORT_NUMBERS.
    """
    if mask_short_numbers is None:
        mask_short_numbers = getattr(settings, "EVENT_MASK_SHORT_NUMBERS", False)
    value = unicodedata.normalize("NFKC", text or "").casefold()
    for pattern, placeholder in _MASKS:
        value = pattern.sub(placeholder, value)
    if mask_short_numbers:
        value = _ANY_NUMBER.sub("<num>", value)
    return _SPACES.sub(" ", value).strip(" \t\n.,;:!-")


def _as_text(value) -> str:
    return str(getattr(value, "value", value) or "")


def compute_fingerprint(
    *,
    event_type=None,
    origin,
    source_name=None,
    service_code=None,
    title=None,
    message=None,
    payload=None,
) -> str:
    """Calcula un fingerprint SHA-256 canónico y versionado para deduplicación."""
    parts = {
        "version": FINGERPRINT_VERSION,
        "event_type": _as_text(event_type),
        "origin": _as_text(origin),
        "source_name": normalize_text(source_name) if source_name else "",
        "service_code": _as_text(service_code),
        "title": normalize_text(title),
        "message": normalize_text(message),
    }

    if payload is not None:
        parts["payload"] = _normalize_payload(payload)

    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
