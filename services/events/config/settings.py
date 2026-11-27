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
    # La frontera de confianza es el gateway; las llamadas internas llegan ya filtradas.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "EXCEPTION_HANDLER": "events.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Help-Chair Events Service API (Contrato v1)",
    "DESCRIPTION": (
        "Contrato de Eventos v1 congelado. Cubre el registro, la deduplicación, el listado, "
        "el detalle, la actualización, las transiciones de estado y el historial de eventos. "
        "JWT Bearer o X-API-Key son validados en el gateway; el servicio permite tráfico "
        "interno directo sin credenciales. Catálogo, SLA, recurrencia y fuentes quedan "
        "fuera del alcance de v1."
    ),
    "VERSION": "1.0.0",
    "SERVERS": [
        {"url": "/api/events/v1", "description": "API Gateway (externo)"},
        {"url": "/api/v1", "description": "Servicio directo (interno)"},
    ],
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SECURITY": [{"bearerAuth": []}, {"apiKeyAuth": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
            "apiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            },
        }
    },
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
# --- Publicación al broker (outbox + NATS JetStream, docs/outbox.md) ---
# Vacío = los mensajes se acumulan en outbox_message y `publish_outbox` falla avisando.
BROKER_URL = env("BROKER_URL", default="")
OUTBOX_STREAM = env("OUTBOX_STREAM", default="EVENTS")
OUTBOX_STREAM_MAX_AGE_DAYS = env.int("OUTBOX_STREAM_MAX_AGE_DAYS", default=7)
OUTBOX_PUBLISH_TIMEOUT_SECONDS = env.float("OUTBOX_PUBLISH_TIMEOUT_SECONDS", default=5.0)
OUTBOX_BATCH_SIZE = env.int("OUTBOX_BATCH_SIZE", default=50)
OUTBOX_MAX_ATTEMPTS = env.int("OUTBOX_MAX_ATTEMPTS", default=10)
OUTBOX_BACKOFF_BASE_SECONDS = env.int("OUTBOX_BACKOFF_BASE_SECONDS", default=5)
OUTBOX_BACKOFF_MAX_SECONDS = env.int("OUTBOX_BACKOFF_MAX_SECONDS", default=900)
OUTBOX_POLL_INTERVAL_SECONDS = env.float("OUTBOX_POLL_INTERVAL_SECONDS", default=2.0)
# Transporte: `jetstream` (por omisión) o `http` (plan B: POST síncrono, misma interfaz).
OUTBOX_TRANSPORT = env("OUTBOX_TRANSPORT", default="jetstream")
# Plan B: `patrón=url1,url2;patrón=url3` (comodines de NATS en el patrón). Ver docs/outbox.md.
OUTBOX_HTTP_ROUTES = env("OUTBOX_HTTP_ROUTES", default="")
OUTBOX_HTTP_TOKEN = env("OUTBOX_HTTP_TOKEN", default="")

# --- Deduplicación ---
# Etapa 1 (siempre): misma huella normalizada. Etapa 2 (opcional): similitud Jaro-Winkler.
EVENT_FUZZY_ENABLED = env.bool("EVENT_FUZZY_ENABLED", default=False)
EVENT_FUZZY_THRESHOLD = env.float("EVENT_FUZZY_THRESHOLD", default=0.95)
EVENT_FUZZY_TOKEN_THRESHOLD = env.float("EVENT_FUZZY_TOKEN_THRESHOLD", default=0.88)
EVENT_FUZZY_MAX_DIFF_TOKENS = env.int("EVENT_FUZZY_MAX_DIFF_TOKENS", default=1)
EVENT_FUZZY_MIN_LENGTH = env.int("EVENT_FUZZY_MIN_LENGTH", default=20)
EVENT_FUZZY_MAX_CANDIDATES = env.int("EVENT_FUZZY_MAX_CANDIDATES", default=50)
EVENT_FUZZY_TYPES = env.list("EVENT_FUZZY_TYPES", default=["WARNING", "INFORMATION"])
# True: también enmascara números cortos al normalizar (más fusiones, más riesgo de over-merge).
EVENT_MASK_SHORT_NUMBERS = env.bool("EVENT_MASK_SHORT_NUMBERS", default=False)

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
