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

# Base de datos propia del servicio (database per service).
# Sin DATABASE_URL se usa SQLite: permite `make test` sin levantar PostgreSQL.
# Un DATABASE_URL vacío (p. ej. copiado de .env.example) cuenta como "no definido".
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
        "Contrato de Eventos v1 congelado. Cubre el registro, la deduplicación, el listado y el "
        "detalle de eventos. JWT Bearer o X-API-Key son validados en el gateway; el servicio "
        "permite tráfico interno directo sin credenciales. Las rutas del borrador v0 aún no "
        "implementadas (actualización/reclasificación, transiciones, historial, catálogo, SLA, "
        "recurrencia y fuentes) quedan fuera del alcance de v1."
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
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO").upper()},
}
