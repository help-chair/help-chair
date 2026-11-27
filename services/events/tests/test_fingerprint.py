"""Normalización del mensaje y huella: los duplicados parciales comparten huella."""

import pytest

from events.services.fingerprint import compute_fingerprint, normalize_text

BASE = {
    "event_type": "WARNING",
    "origin": "SYSTEM",
    "source_name": "nagios",
    "service_code": "pagos",
    "title": "Latencia alta",
    "message": "Timeout de 5003 ms conectando a 10.0.0.12:5432 a las 2026-11-20T10:00:00Z",
}


def fp(**overrides):
    return compute_fingerprint(**{**BASE, **overrides})


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Error   EN  el   Servidor.  ", "error en el servidor"),
        ("pedido 7c9e6679-7425-40de-944b-e07fc1f90ae7 falló", "pedido <uuid> falló"),
        ("desde 10.0.0.12:5432 hacia 192.168.1.5", "desde <ip> hacia <ip>"),
        ("a las 2026-11-20T10:00:00Z y 2026-11-21 y 10:45", "a las <ts> y <date> y <time>"),
        ("tardó 5003 ms y usó 95% de 12.5 GB", "tardó <qty> y usó <qty> de <qty>"),
        ("puntero 0x7ffd5c3a y hash deadbeef01", "puntero <hex> y hash <hex>"),
        ("usuario 1234567 bloqueado", "usuario <num> bloqueado"),
    ],
)
def test_volatile_data_is_masked(raw, expected):
    assert normalize_text(raw, mask_short_numbers=False) == expected


def test_short_numbers_are_kept_by_default_to_avoid_over_merging():
    assert normalize_text("estado 500", mask_short_numbers=False) == "estado 500"
    assert normalize_text("estado 500", mask_short_numbers=False) != normalize_text(
        "estado 404", mask_short_numbers=False
    )
    assert normalize_text("estado 500", mask_short_numbers=True) == "estado <num>"


def test_partial_duplicates_share_the_fingerprint():
    other = "Timeout de 4890 ms conectando a 10.0.0.99:5432 a las 2026-11-21T08:30:00Z"
    assert fp(message=other) == fp()
    assert fp(message=other.upper()) == fp()


def test_fingerprint_is_stable_and_has_64_hex_chars():
    assert fp() == fp()
    assert len(fp()) == 64 and set(fp()) <= set("0123456789abcdef")


@pytest.mark.parametrize(
    "change",
    [
        {"event_type": "EXCEPTION"},
        {"origin": "USER"},
        {"source_name": "zabbix"},
        {"service_code": "correo"},
        {"title": "Latencia crítica"},
        {"message": "Timeout de 5003 ms conectando a 10.0.0.12:5432 en la réplica"},
    ],
)
def test_real_differences_change_the_fingerprint(change):
    assert fp(**change) != fp()
