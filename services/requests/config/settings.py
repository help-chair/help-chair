"""Ajustes del servicio requests. Todo se configura por variables de entorno."""

import sys
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Lee .env si existe (solo desarrollo local). En contenedores se usan variables reales.
environ.Env.read_env(BASE_DIR / ".env")

SERVICE_NAME = env("SERVICE_NAME", default="requests")
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
    "peticiones",
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

JWT_AUTH_ENABLED = env.bool("JWT_AUTH_ENABLED", default=False)
JWT_PUBLIC_KEY = env("JWT_PUBLIC_KEY", default="").replace("\\n", "\n")
JWT_SIGNING_KEY = env("JWT_SIGNING_KEY", default=SECRET_KEY)

SIMPLE_JWT = {
    "ALGORITHM": "RS256" if JWT_PUBLIC_KEY else "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "VERIFYING_KEY": JWT_PUBLIC_KEY or None,
    "USER_ID_CLAIM": "sub",
    "ISSUER": env("JWT_ISSUER", default="help-chair-access"),
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "peticiones.permissions.OptionalAccessJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "peticiones.permissions.RequestsServicePermission",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Help Chair - requests",
    "DESCRIPTION": "API del servicio requests (contrato en contracts/requests/).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO").upper()},
}

BROKER_URL = env("BROKER_URL", default="")
BROKER_EVENTS_SUBJECT = env("BROKER_EVENTS_SUBJECT", default="events.routed.requests")
