"""Ajustes del servicio knowledge. Todo se configura por variables de entorno."""

from pathlib import Path

import environ

from config.environment import database_config, read_value, required
from config.logging import logging_config

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
SERVICE_NAME = env("SERVICE_NAME", default="knowledge")
DEBUG = read_value("DEBUG", lambda: env.bool("DEBUG", default=False))
SECRET_KEY = required("SECRET_KEY")

# El gateway de Plataforma es quien filtra el dominio; en K8s las sondas usan la IP del pod.
required("ALLOWED_HOSTS")
ALLOWED_HOSTS = read_value("ALLOWED_HOSTS", lambda: env.list("ALLOWED_HOSTS"))

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
    "articles",
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

# PostgreSQL explícito; ni archivos .env ni un motor alternativo implícito.
DATABASES = {"default": database_config()}
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
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Help Chair - knowledge",
    "DESCRIPTION": "API del servicio knowledge (contrato en contracts/knowledge/).",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = logging_config()
