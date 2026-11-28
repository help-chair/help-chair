"""Configuración explícita del futuro integrador; no activa autenticación."""

import os
import secrets
import subprocess
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.environment import identity_config


@pytest.fixture
def identity_environment(monkeypatch):
    values = {
        "JWKS_URL": "https://identity.test/api/access/v1/.well-known/jwks.json",
        "JWT_ISSUER": secrets.token_hex(16),
        "EMPRESA_ID": secrets.token_hex(16),
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values


@pytest.mark.parametrize("name", ["JWKS_URL", "JWT_ISSUER", "EMPRESA_ID"])
@pytest.mark.parametrize("value", [None, "", " "])
def test_identity_config_requires_each_value_without_disclosure(
    identity_environment, monkeypatch, name, value
):
    if value is None:
        monkeypatch.delenv(name)
    else:
        monkeypatch.setenv(name, value)
    with pytest.raises(ImproperlyConfigured) as failure:
        identity_config()
    assert str(failure.value) == name


@pytest.mark.parametrize(
    "url",
    [
        "ftp://identity.test/.well-known/jwks.json",
        "https:///.well-known/jwks.json",
        "https://user@identity.test/.well-known/jwks.json",
        "https://identity.test/.well-known/jwks.json?private=1",
        "https://identity.test/.well-known/jwks.json#private",
        "https://identity.test/other",
        "https://identity.test:0/.well-known/jwks.json",
        "https://identity.test:65536/.well-known/jwks.json",
        "https://identity.test:bad/.well-known/jwks.json",
        "https://[broken/.well-known/jwks.json",
        "https://identity.test/.well-known/jwks.json ",
        "https://identity.\ttest/.well-known/jwks.json",
    ],
)
def test_identity_config_rejects_invalid_destination_safely(identity_environment, monkeypatch, url):
    monkeypatch.setenv("JWKS_URL", url)
    with pytest.raises(ImproperlyConfigured, match="^JWKS_URL$"):
        identity_config()


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_identity_config_returns_exact_explicit_context(identity_environment, monkeypatch, scheme):
    url = scheme + "://identity.test:8002/api/access/v1/.well-known/jwks.json"
    monkeypatch.setenv("JWKS_URL", url)
    assert identity_config() == {
        "url": url,
        "issuer": identity_environment["JWT_ISSUER"],
        "company": identity_environment["EMPRESA_ID"],
    }


def test_helper_import_does_not_require_django_runtime_configuration():
    environment = {
        name: value
        for name, value in os.environ.items()
        if name
        not in {
            "DJANGO_SETTINGS_MODULE",
            "SECRET_KEY",
            "DATABASE_URL",
            "ALLOWED_HOSTS",
            "JWKS_URL",
            "JWT_ISSUER",
            "EMPRESA_ID",
        }
    }
    result = subprocess.run(
        [sys.executable, "-c", "from config.environment import identity_config"],
        env=environment,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, "El helper no debe cargar los ajustes de runtime"
