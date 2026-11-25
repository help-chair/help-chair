"""JSON a stderr sin DSN, cabeceras de autenticación ni detalles de excepciones."""

import json
import logging
import os
import re
import time

from django.core.exceptions import ImproperlyConfigured

_URL = re.compile(r"[a-z][a-z0-9+.-]*://[^\s<>\"']+", re.IGNORECASE)
_QUERY = re.compile(r"(?:/[^\s<>\"']*)?\?[^\s<>\"']+")
_HEADER = re.compile(r"\b(?:authorization|proxy-authorization|cookie|set-cookie)\s*[:=].*", re.I)
_AUTH = re.compile(r"\b(?:Bearer|Basic)\s+\S+", re.I)
_ASSIGNMENT = re.compile(r"\b(?:password|passwd|secret_key|token|api_key)\s*[:=]\s*[^\s,;]+", re.I)


def redact(message):
    for name, value in os.environ.items():
        if value and any(
            part in name.upper()
            for part in ("SECRET", "PASSWORD", "TOKEN", "API_KEY", "PRIVATE_KEY")
        ):
            message = message.replace(value, "[redacted]")
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        message = message.replace(database_url, "[redacted]")
    for pattern in (_URL, _QUERY, _HEADER, _AUTH, _ASSIGNMENT):
        message = pattern.sub("[redacted]", message)
    return message


class JsonFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record):
        if record.name.startswith("django.request"):
            message = "request_error"
        elif record.name.startswith("django.server"):
            message = "http_request"
        else:
            message = redact(record.getMessage())
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "service": os.environ.get("SERVICE_NAME", "problems"),
            "message": message,
        }
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
            error = record.exc_info[1]
            if isinstance(error, ImproperlyConfigured) and str(error) in {
                "SECRET_KEY",
                "DATABASE_URL",
                "ALLOWED_HOSTS",
                "DEBUG",
                "LOG_LEVEL",
                "PORT",
                "WEB_CONCURRENCY",
                "GRACEFUL_TIMEOUT",
                "DATABASE_CONNECT_TIMEOUT",
            }:
                payload["configuration"] = str(error)
        return json.dumps(payload, ensure_ascii=False)


def logging_config():
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ImproperlyConfigured("LOG_LEVEL")
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "json",
            }
        },
        "root": {"handlers": ["console"], "level": level},
        "loggers": {
            name: {"handlers": ["console"], "level": level, "propagate": False}
            for name in (
                "django",
                "django.request",
                "django.server",
                "gunicorn.error",
                "gunicorn.access",
            )
        },
    }
