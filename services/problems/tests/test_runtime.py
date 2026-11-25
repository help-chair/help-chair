import json
import logging
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.logging import JsonFormatter

SERVICE = Path(__file__).resolve().parents[1]
CONFIG_VARS = ("SECRET_KEY", "DATABASE_URL", "ALLOWED_HOSTS")


def settings_result(environment, directory=SERVICE, prefix=""):
    return subprocess.run(
        [
            sys.executable,
            "-c",
            prefix + "from config import settings; print(settings.DATABASES['default']['ENGINE'])",
        ],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )


@pytest.mark.parametrize("name", CONFIG_VARS)
@pytest.mark.parametrize("empty", [False, True])
def test_runtime_requires_explicit_variables_without_revealing_values(name, empty):
    environment = os.environ.copy()
    if empty:
        environment[name] = " "
    else:
        environment.pop(name, None)
    result = settings_result(environment)
    failure_is_safe = (
        result.returncode != 0
        and result.stderr.rstrip().endswith(f"ImproperlyConfigured: {name}")
        and all(os.environ[key] not in result.stderr for key in ("SECRET_KEY", "DATABASE_URL"))
    )
    assert failure_is_safe, "Missing configuration must fail with the variable name only"


@pytest.mark.parametrize("kind", ["sqlite", "malformed", "missing_password"])
def test_runtime_rejects_non_postgresql_or_invalid_dsn_safely(kind):
    from urllib.parse import urlsplit, urlunsplit

    environment = os.environ.copy()
    if kind == "sqlite":
        environment["DATABASE_URL"] = "sqlite:///rejected.db"
    elif kind == "malformed":
        environment["DATABASE_URL"] = secrets.token_urlsafe(40)
    else:
        url = urlsplit(environment["DATABASE_URL"])
        environment["DATABASE_URL"] = urlunsplit(
            (url.scheme, f"{url.username}@{url.netloc.rsplit('@', 1)[-1]}", url.path, "", "")
        )
    result = settings_result(environment)
    failure_is_safe = (
        result.returncode != 0
        and result.stderr.rstrip().endswith("ImproperlyConfigured: DATABASE_URL")
        and environment["DATABASE_URL"] not in result.stderr
    )
    assert failure_is_safe, "Invalid database configuration must not expose its value"


def test_dotenv_is_not_loaded_even_when_it_contains_all_required_variables(tmp_path):
    shutil.copytree(SERVICE / "config", tmp_path / "config")
    private_file = tmp_path / ".env"
    private_file.write_text(
        "\n".join(f"{name}={os.environ[name]}" for name in CONFIG_VARS), encoding="utf-8"
    )
    private_file.chmod(0o600)
    environment = {name: value for name, value in os.environ.items() if name not in CONFIG_VARS}
    result = settings_result(environment, tmp_path)
    no_automatic_configuration = result.returncode != 0 and result.stderr.rstrip().endswith(
        "ImproperlyConfigured: SECRET_KEY"
    )
    assert no_automatic_configuration, "A local .env must not configure the service"


def test_runtime_selects_postgresql_from_the_process_environment():
    result = settings_result(os.environ.copy())
    explicit_postgresql = (
        result.returncode == 0 and result.stdout.strip() == "django.db.backends.postgresql"
    )
    assert explicit_postgresql, "The runtime must use the configured PostgreSQL engine"


@pytest.mark.parametrize("mode", ["debug", "pytest"])
def test_debug_or_pytest_does_not_enable_a_default_secret(mode):
    environment = os.environ.copy()
    environment.pop("SECRET_KEY", None)
    environment["DEBUG"] = "true" if mode == "debug" else "false"
    prefix = "import sys; sys.modules['pytest'] = object(); " if mode == "pytest" else ""
    result = settings_result(environment, prefix=prefix)
    no_default = result.returncode != 0 and result.stderr.rstrip().endswith(
        "ImproperlyConfigured: SECRET_KEY"
    )
    assert no_default, "Development and tests must still require an explicit private key"


@pytest.mark.parametrize("logger", ["core.views", "django.request", "django.server"])
def test_json_logging_does_not_publish_secrets_urls_headers_or_exception_text(logger, monkeypatch):
    private_value = secrets.token_urlsafe(40)
    monkeypatch.setenv("SERVICE_TEST_TOKEN", private_value)
    message = (
        f"{private_value} {os.environ['DATABASE_URL']} "
        f"https://localhost/?token={private_value} Authorization: Bearer {private_value}"
    )
    error = RuntimeError(message)
    record = logging.LogRecord(logger, logging.ERROR, __file__, 1, message, (), None)
    record.exc_info = (RuntimeError, error, None)
    output = JsonFormatter().format(record)
    payload = json.loads(output)
    sanitized = all(
        value not in output
        for value in (private_value, os.environ["DATABASE_URL"], "Authorization", "?token=")
    )
    assert sanitized, "JSON logging must not disclose private input"
    assert payload["exception_type"] == "RuntimeError"
    assert "exc_info" not in payload


@pytest.mark.parametrize("header", ["Cookie", "Set-Cookie", "Proxy-Authorization"])
def test_json_logging_suppresses_authentication_headers(header):
    private_value = secrets.token_urlsafe(40)
    record = logging.LogRecord(
        "core.views", logging.INFO, __file__, 1, f"{header}: {private_value}", (), None
    )
    output = JsonFormatter().format(record)
    sanitized = private_value not in output and header not in output
    assert sanitized, "Authentication headers must not appear in logs"


def test_gunicorn_error_does_not_disclose_relative_query_credentials():
    private_value = secrets.token_urlsafe(40)
    record = logging.LogRecord(
        "gunicorn.error",
        logging.ERROR,
        __file__,
        1,
        f"Invalid URI /callback?code={private_value}",
        (),
        None,
    )
    output = JsonFormatter().format(record)
    sanitized = private_value not in output and "?code=" not in output
    assert sanitized, "Relative request queries must not appear in gunicorn errors"


def test_configuration_log_reports_only_the_allowed_variable_name():
    record = logging.LogRecord(
        "gunicorn.error", logging.ERROR, __file__, 1, "worker failed", (), None
    )
    record.exc_info = (ImproperlyConfigured, ImproperlyConfigured("SECRET_KEY"), None)
    assert json.loads(JsonFormatter().format(record))["configuration"] == "SECRET_KEY"


@pytest.mark.parametrize("canonical", [False, True])
def test_schema_export_refuses_missing_destination_or_contract_overwrite(canonical):
    environment = os.environ.copy()
    environment.pop("OPENAPI_OUTPUT", None)
    if canonical:
        environment["OPENAPI_OUTPUT"] = str(
            SERVICE.parents[1] / "contracts" / "problems" / "openapi.yaml"
        )
    result = subprocess.run(
        [sys.executable, "scripts/export_schema.py"],
        cwd=SERVICE,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert result.stderr.startswith("OPENAPI_OUTPUT:")
