"""Tokens firmados con RSA efímera, sin credenciales ni llamadas a Accesos."""

import json
import secrets
import time
from dataclasses import FrozenInstanceError
from urllib.error import URLError
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core import jwks
from core.identity import AccessAuthentication, AccessAuthenticationScheme


class Probe(APIView):
    authentication_classes = [AccessAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"id": request.user.pk, "claims": request.auth})


@pytest.fixture(scope="module")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def context(settings, monkeypatch, private_key):
    config = {"url": "https://identity.test/keys", "issuer": "access-test", "company": "test"}
    settings.ACCESS_IDENTITY = config
    item = jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    item.update(kid="first", alg="RS256", use="sig")
    calls = []

    def fetch(url):
        calls.append(url)
        return {"keys": [item]}

    monkeypatch.setattr(jwks, "download_keys", fetch)
    jwks.key_cache.cache_clear()
    now = int(time.time())
    claims = dict(
        sub=str(uuid4()),
        exp=now + 300,
        iat=now - 1,
        iss=config["issuer"],
        empresa=config["company"],
        rol="agente_n1",
        permisos=["tickets:ver"],
        token_type="access",
    )
    yield claims, calls
    jwks.key_cache.cache_clear()


def signed(private_key, claims, **headers):
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "first", **headers})


def invoke(token=None):
    kwargs = {} if token is None else {"HTTP_AUTHORIZATION": "Bearer " + token}
    return Probe.as_view()(APIRequestFactory().get("/probe", **kwargs))


def test_explicit_drf_authentication_and_immutable_identity(context, private_key):
    claims, calls = context
    token = signed(private_key, claims)
    response = invoke(token)
    assert response.status_code == 200 and response.data["claims"] == claims
    identity, decoded = AccessAuthentication().authenticate(
        APIRequestFactory().get("/probe", HTTP_AUTHORIZATION="Bearer " + token)
    )
    assert identity.pk == claims["sub"] and identity.company == "test"
    assert identity.is_authenticated and not identity.is_anonymous
    assert identity.permissions == frozenset({"tickets:ver"}) and decoded == claims
    with pytest.raises(FrozenInstanceError):
        identity.role = "administrador"
    assert calls == ["https://identity.test/keys"]
    assert AccessAuthenticationScheme(None).get_security_definition(None) == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }


@pytest.mark.parametrize(
    "field", ["sub", "exp", "iat", "iss", "empresa", "rol", "permisos", "token_type"]
)
def test_required_claims(context, private_key, field):
    claims, _ = context
    claims.pop(field)
    assert_rejected(signed(private_key, claims))


@pytest.mark.parametrize(
    "field,value",
    [
        ("sub", "not-a-uuid"),
        ("sub", 12),
        ("iss", "foreign"),
        ("empresa", "foreign"),
        ("empresa", None),
        ("rol", "invented"),
        ("rol", []),
        ("token_type", "refresh"),
        ("exp", 0),
        ("iat", 9999999999),
        ("exp", True),
        ("iat", False),
        ("exp", "9999999999"),
        ("iat", "0"),
        ("exp", float("inf")),
        ("iat", float("nan")),
        ("permisos", "tickets:ver"),
        ("permisos", ["invented"]),
        ("permisos", ["tickets:ver", "tickets:ver"]),
        ("permisos", [[]]),
        ("aud", "arbitrary"),
        ("aud", ["arbitrary"]),
    ],
)
def test_invalid_claims(context, private_key, field, value):
    claims, _ = context
    claims[field] = value
    assert_rejected(signed(private_key, claims))


def assert_rejected(token):
    response = invoke(token)
    assert response.status_code == 401
    assert response.data == {
        "codigo": "no_autenticado",
        "detalle": "Identidad de Accesos no válida.",
    }
    assert response["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "metadata",
    [
        {"kid": ""},
        {"kid": "a/b"},
        {"kid": "x" * 129},
        {"kid": 1},
        {"jku": "https://attacker.test"},
        {"jwk": {}},
        {"x5u": "https://attacker.test"},
        {"crit": []},
        {"b64": True},
    ],
)
def test_untrusted_headers_never_fetch(context, private_key, metadata):
    claims, calls = context
    # PyJWT rechaza kid numérico y elimina b64=True al firmar: alterar el sobre
    # permite probar la cabecera recibida, que debe fallar antes de buscar clave.
    token = signed(private_key, claims).split(".")
    header = {"alg": "RS256", "kid": "first", **metadata}
    token[0] = jwt.utils.base64url_encode(json.dumps(header).encode()).decode()
    assert_rejected(".".join(token))
    assert calls == []


@pytest.mark.parametrize("header", ["Basic abc", "Bearer", "Bearer a b", "Bearer " + "x" * 16385])
def test_malformed_authorization_never_fetch(context, header):
    _, calls = context
    response = Probe.as_view()(APIRequestFactory().get("/probe", HTTP_AUTHORIZATION=header))
    assert response.status_code == 401 and calls == []


def test_no_token_and_wrong_algorithm(context):
    claims, calls = context
    assert invoke().status_code == 401
    assert_rejected(jwt.encode(claims, secrets.token_bytes(48), algorithm="HS256"))
    assert_rejected("malformed")
    assert calls == []


def test_bad_signature_unknown_key_and_inverted_dates(context, private_key):
    claims, _ = context
    foreign = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert_rejected(signed(foreign, claims))
    assert_rejected(signed(private_key, claims, kid="unknown"))
    claims["iat"] = claims["exp"]
    assert_rejected(signed(private_key, claims))


@pytest.mark.parametrize("error", [ValueError(), URLError("private failure"), TimeoutError()])
def test_jwks_failure_is_generic(context, private_key, monkeypatch, error):
    claims, _ = context

    def fail(url):
        raise error

    monkeypatch.setattr(jwks, "download_keys", fail)
    assert_rejected(signed(private_key, claims))


def test_missing_config_fails_closed(context, private_key, settings):
    claims, _ = context
    del settings.ACCESS_IDENTITY
    assert_rejected(signed(private_key, claims))


def test_empty_permissions_and_each_real_role(context, private_key):
    claims, _ = context
    for role in ("administrador", "agente_n1", "agente_n2", "usuario_final"):
        claims.update(rol=role, permisos=[])
        assert invoke(signed(private_key, claims)).status_code == 200
