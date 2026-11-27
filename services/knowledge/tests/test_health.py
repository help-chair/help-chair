import secrets

import pytest

from core import views


def test_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_ready_ok(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "up"


def test_ready_returns_503_when_the_database_fails(client, monkeypatch, caplog):
    private_value = secrets.token_urlsafe(40)

    def boom():
        raise RuntimeError(private_value)

    monkeypatch.setattr(views, "check_database", boom)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}
    assert client.get("/health/live").status_code == 200
    sanitized = private_value not in caplog.text
    assert sanitized, "Readiness must not log database exception details"
