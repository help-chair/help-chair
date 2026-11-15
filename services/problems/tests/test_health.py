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


def test_ready_devuelve_503_si_la_bd_falla(client, monkeypatch):
    def boom():
        raise RuntimeError("bd caida")

    monkeypatch.setattr(views, "check_database", boom)
    response = client.get("/health/ready")
    assert response.status_code == 503
