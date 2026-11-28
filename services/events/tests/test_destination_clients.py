import httpx
import pytest

from events.clients.base import (
    DestinationError,
    DestinationNotConfigured,
    ServiceTokenProvider,
)
from events.clients.destinations import IncidentsClient, ProblemsClient
from tests.factories import make_event

pytestmark = pytest.mark.django_db


def make_client(cls, handler, **kw):
    kw.setdefault("base_url", "http://destino")
    return cls(
        token_provider=ServiceTokenProvider(static_token="jwt-de-prueba"),
        transport=httpx.MockTransport(handler),
        sleep=lambda s: None,
        timeout=1,
        retries=2,
        backoff=0,
        **kw,
    )


def test_incident_payload_headers_and_remote_id():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["Authorization"]
        seen["key"] = request.headers["Idempotency-Key"]
        seen["body"] = request.read()
        return httpx.Response(201, json={"id": 17, "code": "INC-000017"})

    event = make_event(impact="HIGH", urgency="LOW")
    result = make_client(IncidentsClient, handler).create(event, rule_code="R6")

    assert result.remote_id == "17"
    assert seen["auth"] == "Bearer jwt-de-prueba"
    assert seen["key"] == str(event.pk)
    assert b'"impact":"alto"' in seen["body"].replace(b" ", b"")
    assert str(event.pk).encode() in seen["body"]


def test_retries_on_5xx_then_succeeds():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503) if len(calls) < 3 else httpx.Response(201, json={"id": 1})

    result = make_client(ProblemsClient, handler).create(make_event(), rule_code="R7")
    assert result.remote_id == "1"
    assert len(calls) == 3


def test_does_not_retry_on_4xx():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(400, json={"codigo": "datos_invalidos"})

    with pytest.raises(DestinationError) as exc:
        make_client(ProblemsClient, handler).create(make_event(), rule_code="R7")
    assert exc.value.retryable is False
    assert len(calls) == 1


def test_timeout_is_retryable_and_gives_up_after_retries():
    calls = []

    def handler(request):
        calls.append(1)
        raise httpx.ConnectTimeout("lento")

    with pytest.raises(DestinationError) as exc:
        make_client(IncidentsClient, handler).create(make_event(), rule_code="R6")
    assert exc.value.retryable is True
    assert len(calls) == 3  # 1 intento + 2 reintentos


def test_missing_url_is_reported_without_network():
    client = make_client(IncidentsClient, lambda r: httpx.Response(500), base_url="")
    with pytest.raises(DestinationNotConfigured):
        client.create(make_event(), rule_code="R6")


def test_expired_token_is_refreshed_once_on_401():
    tokens = iter(["viejo", "nuevo"])
    logins = []

    def login_handler(request):
        logins.append(1)
        return httpx.Response(200, json={"acceso": next(tokens), "expira_en": 900})

    provider = ServiceTokenProvider(
        access_url="http://access",
        email="svc@x.test",
        password="x",
        transport=httpx.MockTransport(login_handler),
    )
    auths = []

    def handler(request):
        auths.append(request.headers["Authorization"])
        return httpx.Response(401) if len(auths) == 1 else httpx.Response(201, json={"id": 5})

    client = IncidentsClient(
        token_provider=provider,
        base_url="http://destino",
        transport=httpx.MockTransport(handler),
        timeout=1,
        retries=0,
        backoff=0,
    )
    assert client.create(make_event(), rule_code="R6").remote_id == "5"
    assert auths == ["Bearer viejo", "Bearer nuevo"]
    assert len(logins) == 2
