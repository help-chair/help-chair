"""JWKS con claves efímeras y transporte HTTP real limitado a loopback."""

import copy
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from core import jwks


@pytest.fixture(scope="module")
def document():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    item = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    item.update(kid="first", alg="RS256", use="sig")
    return {"keys": [item]}


@pytest.mark.parametrize(
    "field,value",
    [
        ("kty", "EC"),
        ("alg", "HS256"),
        ("use", "enc"),
        ("e", "Aw"),
        ("n", "!"),
        ("n", "x" * 1367),
        ("kid", ""),
        ("kid", "x" * 129),
        ("kid", "a/b"),
        ("kid", "a\n"),
        ("key_ops", ["sign"]),
        *[(field, "") for field in ("d", "p", "q", "dp", "dq", "qi", "oth")],
    ],
)
def test_rejects_unsafe_key(document, field, value):
    candidate = copy.deepcopy(document)
    candidate["keys"][0][field] = value
    with pytest.raises((ValueError, jwt.PyJWTError)):
        jwks.public_keys(candidate)


@pytest.mark.parametrize(
    "candidate", [None, [], {}, {"keys": {}}, {"keys": []}, {"keys": [None]}, {"keys": [{}] * 17}]
)
def test_rejects_shape(candidate):
    with pytest.raises(ValueError):
        jwks.public_keys(candidate)


def test_size_duplicates_and_valid_public_key(document):
    assert jwks.public_keys(document)["first"].key_size == 2048
    item = document["keys"][0]
    with pytest.raises(ValueError):
        jwks.public_keys({"keys": [item, item]})
    small = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    weak = jwt.algorithms.RSAAlgorithm.to_jwk(small.public_key(), as_dict=True)
    with pytest.raises(ValueError):
        jwks.public_keys({"keys": [{**item, **weak}]})
    assert jwks.public_keys({"keys": [{**item, "key_ops": ["verify"]}]})


@pytest.fixture
def clock(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(jwks.time, "monotonic", lambda: now[0])
    return now


def test_rotation_expiry_and_throttle(document, monkeypatch, clock):
    calls = []
    current = copy.deepcopy(document)

    def fetch(url):
        calls.append(url)
        return current

    monkeypatch.setattr(jwks, "download_keys", fetch)
    cache = jwks.KeyCache("configured-destination")
    first = cache.key("first")
    assert cache.key("first") is first and len(calls) == 1
    for _ in range(3):
        with pytest.raises(ValueError):
            cache.key("unknown")
    assert len(calls) == 1
    clock[0] += jwks.REFRESH_SECONDS
    current["keys"][0]["kid"] = "rotated"
    assert cache.key("rotated").key_size == 2048 and len(calls) == 2
    with pytest.raises(ValueError):
        cache.key("first")
    clock[0] += jwks.CACHE_SECONDS
    monkeypatch.setattr(jwks, "download_keys", lambda url: (_ for _ in ()).throw(URLError("")))
    with pytest.raises(ValueError):
        cache.key("rotated")
    with pytest.raises(ValueError):
        cache.key("rotated")  # El fallo no extiende la vigencia anterior.
    clock[0] += jwks.REFRESH_SECONDS
    monkeypatch.setattr(jwks, "download_keys", fetch)
    assert cache.key("rotated").key_size == 2048


def test_concurrent_refresh(document, monkeypatch, clock):
    calls = []
    barrier = threading.Barrier(8)

    def fetch(url):
        calls.append(url)
        return document

    def read(_):
        barrier.wait(timeout=3)
        return cache.key("first")

    monkeypatch.setattr(jwks, "download_keys", fetch)
    cache = jwks.KeyCache("configured-destination")
    with ThreadPoolExecutor(max_workers=8) as pool:
        keys = list(pool.map(read, range(8)))
    assert len(calls) == 1 and all(key is keys[0] for key in keys)


def test_factory_is_bounded():
    jwks.key_cache.cache_clear()
    assert jwks.key_cache("one") is jwks.key_cache("one")
    assert jwks.key_cache("one") is not jwks.key_cache("two")
    for number in range(8):
        jwks.key_cache(str(number))
    assert jwks.key_cache.cache_info().currsize == 4
    jwks.key_cache.cache_clear()


@pytest.fixture
def server(document):
    paths = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            paths.append(self.path)
            if self.path == "/slow":
                time.sleep(0.1)
            status = 302 if self.path == "/redirect" else 200
            self.send_response(status)
            self.send_header("Location", "/keys")
            self.end_headers()
            body = json.dumps(document).encode()
            if self.path == "/large":
                body = b" " * (jwks.MAX_DOCUMENT + 1)
            if self.path == "/broken":
                body = b"{"
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", paths
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


def test_real_transport(server, document, monkeypatch):
    url, paths = server
    for name in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, "http://127.0.0.1:1")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setenv("NO_PROXY", "")
    assert jwks.download_keys(url + "/keys") == document
    for path in ("/redirect", "/large", "/broken"):
        cache = jwks.KeyCache(url + path)
        with pytest.raises(ValueError):
            cache.key("first")
        assert cache.keys == {} and cache.expires == 0
    assert paths.count("/keys") == 1  # Ninguna redirección seguida.
    monkeypatch.setattr(jwks, "TIMEOUT", 0.02)
    with pytest.raises(ValueError):
        jwks.KeyCache(url + "/slow").key("first")
