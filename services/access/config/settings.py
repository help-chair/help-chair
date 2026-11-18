"""Ajustes del servicio access. Todo se configura por variables de entorno."""

import sys
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Lee .env si existe (solo desarrollo local). En contenedores se usan variables reales.
environ.Env.read_env(BASE_DIR / ".env")

SERVICE_NAME = env("SERVICE_NAME", default="access")
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
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Forma de error del contrato: {codigo, detalle, campos}.
    "EXCEPTION_HANDLER": "core.errors.manejador_de_errores",
}

# Empresa dueña de este stack. Cada empresa corre su propio stack con su propia
# base de datos, así que la empresa es configuración del despliegue y no una
# tabla que haya que arrastrar en cada modelo.
EMPRESA_ID = env("EMPRESA_ID", default="empresa-demo")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_MINUTOS", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("REFRESH_TOKEN_DIAS", default=1)),
    "UPDATE_LAST_LOGIN": True,
    # El contrato nombra `sub` al identificador del usuario y pide `iss`.
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
    "ISSUER": env("JWT_ISSUER", default="help-chair-access"),
}

# Modelo de usuario propio: se identifica por correo, como dice el contrato.
AUTH_USER_MODEL = "core.Usuario"

# Intentos fallidos de inicio de sesión antes de bloquear la cuenta.
INTENTOS_ANTES_DE_BLOQUEAR = env.int("INTENTOS_ANTES_DE_BLOQUEAR", default=3)

SPECTACULAR_SETTINGS = {
    "TITLE": "Help Chair - access",
    "DESCRIPTION": "API del servicio access (contrato en contracts/access/).",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO").upper()},
}
