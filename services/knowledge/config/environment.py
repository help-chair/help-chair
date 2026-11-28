"""Configuración del proceso: los errores identifican nombres, nunca valores."""

import os
from urllib.parse import urlsplit

import environ
from django.core.exceptions import ImproperlyConfigured


def required(name):
    value = os.environ.get(name, "")
    if not value.strip():
        raise ImproperlyConfigured(name)
    return value


def read_value(name, reader):
    try:
        return reader()
    except (ValueError, TypeError, KeyError, ImproperlyConfigured):
        raise ImproperlyConfigured(name) from None


def positive_integer(name, default, maximum=None):
    value = read_value(name, lambda: int(os.environ.get(name, default)))
    if value < 1 or (maximum is not None and value > maximum):
        raise ImproperlyConfigured(name)
    return value


def database_config():
    def parse():
        value = required("DATABASE_URL")
        url = urlsplit(value)
        if (
            url.scheme not in {"postgres", "postgresql"}
            or not url.hostname
            or not url.username
            or not url.password
            or url.path in {"", "/"}
            or url.fragment
        ):
            raise ImproperlyConfigured("DATABASE_URL")
        config = environ.Env.db_url_config(value)
        if config["ENGINE"] != "django.db.backends.postgresql":
            raise ImproperlyConfigured("DATABASE_URL")
        return config

    config = read_value("DATABASE_URL", parse)
    config.setdefault("OPTIONS", {})["connect_timeout"] = positive_integer(
        "DATABASE_CONNECT_TIMEOUT", 5
    )
    return config


def identity_config():
    url = required("JWKS_URL")
    try:
        parts = urlsplit(url)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.query
            or parts.fragment
            or not parts.path.endswith("/.well-known/jwks.json")
            or parts.port == 0
            or any(c.isspace() for c in url)
        ):
            raise ValueError
    except ValueError:
        raise ImproperlyConfigured("JWKS_URL") from None
    return {"url": url, "issuer": required("JWT_ISSUER"), "company": required("EMPRESA_ID")}
