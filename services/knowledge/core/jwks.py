"""Cliente JWKS acotado; no activa autenticación ni valida claims JWT."""

import json
import re
import threading
import time
from functools import lru_cache
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import jwt

KID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
MAX_DOCUMENT = 65536
TIMEOUT = 3
CACHE_SECONDS = 300
REFRESH_SECONDS = 10


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_keys(url):
    # Sin proxies del entorno ni redirecciones; el JWT nunca elige este destino.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(
        Request(url, headers={"Accept": "application/json"}), timeout=TIMEOUT
    ) as reply:
        if reply.status != 200:
            raise ValueError
        body = reply.read(MAX_DOCUMENT + 1)
    if len(body) > MAX_DOCUMENT:
        raise ValueError
    return json.loads(body)


def public_keys(document):
    if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
        raise ValueError
    if not 1 <= len(document["keys"]) <= 16:
        raise ValueError
    keys = {}
    for item in document["keys"]:
        if (
            not isinstance(item, dict)
            or item.get("kty") != "RSA"
            or item.get("alg") != "RS256"
            or item.get("use") != "sig"
            or not isinstance(item.get("n"), str)
            or len(item["n"]) > 1366
            or item.get("e") != "AQAB"
            or not isinstance(item.get("kid"), str)
            or not KID.fullmatch(item["kid"])
            or item["kid"] in keys
            or any(name in item for name in ("d", "p", "q", "dp", "dq", "qi", "oth"))
            or ("key_ops" in item and item["key_ops"] != ["verify"])
        ):
            raise ValueError
        key = jwt.PyJWK.from_dict(item, algorithm="RS256").key
        if not 2048 <= key.key_size <= 8192:
            raise ValueError
        keys[item["kid"]] = key
    return keys


class KeyCache:
    """Un caché acotado por proceso; un fallo no prolonga la vida de claves viejas."""

    def __init__(self, url):
        self.url = url
        self.keys = {}
        self.expires = 0
        self.retry_at = 0
        self.lock = threading.Lock()

    def key(self, kid):
        with self.lock:
            now = time.monotonic()
            if now < self.expires and kid in self.keys:
                return self.keys[kid]
            if now >= self.retry_at:
                self.retry_at = now + REFRESH_SECONDS
                try:
                    keys = public_keys(download_keys(self.url))
                except (
                    URLError,
                    OSError,
                    HTTPException,
                    ValueError,
                    TypeError,
                    KeyError,
                    RecursionError,
                    OverflowError,
                    jwt.PyJWTError,
                ):
                    raise ValueError from None
                self.keys = keys
                self.expires = time.monotonic() + CACHE_SECONDS
            if time.monotonic() >= self.expires or kid not in self.keys:
                raise ValueError
            return self.keys[kid]


@lru_cache(maxsize=4)
def key_cache(url):
    return KeyCache(url)
