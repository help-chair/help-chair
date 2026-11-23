"""Ajustes del servicio events. Todo se configura por variables de entorno."""

import sys
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Lee .env si existe (solo desarrollo local). En contenedores se usan variables reales.
environ.Env.read_env(BASE_DIR / ".env")

SERVICE_NAME = env("SERVICE_NAME", default="events")
DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG or "pytest" in sys.modules:
        SECRET_KEY = "insecure-dev-key-solo-para-desarrollo"
    else:
        raise ImproperlyConfigured("Define SECRET_KEY (ver .env.example).")

# El gateway de Plataforma es quien filtra el dominio; en K8s las sondas usan la IP del pod.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core",
    "events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASE_URL = env("DATABASE_URL", default="") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {"default": env.db_url_config(DATABASE_URL)}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "events.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Help Chair - events",
    "DESCRIPTION": "API del servicio events (contrato en contracts/events/).",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "POSTPROCESSING_HOOKS": ["events.serializers.contract_required_postprocessing"],
    # El PATCH usa el mismo componente (EventUpdate) que el contrato, no "PatchedEventUpdate".
    "COMPONENT_SPLIT_PATCH": False,
}

# --- Clasificación y vigilancia de eventos (reglas 1 y 3) ---
# Clave del payload donde las fuentes mandan su severidad (info, warning, error...).
EVENT_SEVERITY_KEY = env("EVENT_SEVERITY_KEY", default="severity")
# Umbral de recurrencia por defecto (N veces en T días) cuando no hay una RecurrencePolicy.
EVENT_RECURRENCE_DEFAULT = {
    "threshold_count": env.int("EVENT_THRESHOLD_DEFAULT", default=3),
    "window_days": env.int("EVENT_WINDOW_DAYS_DEFAULT", default=7),
}
# TEMPORAL hasta integrar el JWT de Accesos: permite identificar al actor con la cabecera
# X-Actor-Ref. Es falsificable: NUNCA activarlo en producción.
ALLOW_ACTOR_HEADER = env.bool("ALLOW_ACTOR_HEADER", default=False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO").upper()},
}
