"""Plan B: publicar por REST con la misma interfaz `Publisher` (ROADMAP, fase 2, riesgos).

Si el broker se complica, Eventos entrega cada mensaje con un `POST` síncrono a los servicios
interesados. La lógica de negocio y el outbox no cambian: solo se cambia `OUTBOX_TRANSPORT=http`.
Los reintentos y la espera exponencial siguen siendo los del relay (events/outbox/relay.py).

- **Ruteo:** `OUTBOX_HTTP_ROUTES` asocia patrones de subject (comodines de NATS: `*` = un token,
  `>` = el resto) con una o varias URL. Un subject sin ruta no tiene suscriptores: se da por
  entregado. Formato: `patrón=url1,url2;patrón=url3`.
- **Cuerpo:** el mismo sobre común (contracts/messages/event-envelope.json).
- **Cabeceras:** `Idempotency-Key` = `id` del sobre (el receptor descarta duplicados y responde
  2xx), `X-Message-Subject` y, si se configura, `Authorization: Bearer <OUTBOX_HTTP_TOKEN>`.
- **Respuesta:** 2xx = entregado. Sin conexión, timeout, 408, 429 o 5xx = falla temporal (el
  receptor no está disponible). Cualquier otro 4xx = el receptor rechaza el mensaje (permanente).
- Con varias URL, el mensaje se da por publicado solo si **todas** responden 2xx; al reintentar
  se reenvía a todas y las que ya lo tenían lo descartan por `Idempotency-Key`.
"""

import urllib.error
import urllib.request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .relay import TransientPublishError

TRANSIENT_STATUS = {408, 429}
USER_AGENT = "hc-events-outbox"


class HttpRejected(Exception):
    """El receptor respondió 4xx: el mensaje no se acepta (falla permanente)."""


def parse_routes(raw: str) -> list[tuple[str, list[str]]]:
    """`"events.routed.*=http://a,http://b;events.state_changed=http://c"` -> pares."""
    routes = []
    for entry in filter(None, (part.strip() for part in (raw or "").split(";"))):
        pattern, sep, urls = entry.partition("=")
        targets = [url.strip() for url in urls.split(",") if url.strip()]
        if not sep or not pattern.strip() or not targets:
            raise ImproperlyConfigured(f"OUTBOX_HTTP_ROUTES inválido en {entry!r}")
        for url in targets:
            if not url.startswith(("http://", "https://")):
                raise ImproperlyConfigured(f"OUTBOX_HTTP_ROUTES: URL inválida {url!r}")
        routes.append((pattern.strip(), targets))
    return routes


def subject_matches(pattern: str, subject: str) -> bool:
    """Comodines de NATS: `*` coincide con un token y `>` con uno o más al final."""
    expected, actual = pattern.split("."), subject.split(".")
    for index, token in enumerate(expected):
        if token == ">":
            return len(actual) > index
        if index >= len(actual) or token not in ("*", actual[index]):
            return False
    return len(expected) == len(actual)


class HttpPublisher:
    """Entrega por `POST`. Se usa como contexto igual que JetStreamPublisher (aquí no conecta)."""

    def __init__(self, routes, *, timeout=None, token=None):
        self.routes = routes
        self.timeout = timeout or settings.OUTBOX_PUBLISH_TIMEOUT_SECONDS
        self.token = token if token is not None else settings.OUTBOX_HTTP_TOKEN

    @classmethod
    def from_settings(cls) -> "HttpPublisher":
        return cls(parse_routes(settings.OUTBOX_HTTP_ROUTES))

    def __enter__(self) -> "HttpPublisher":
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def targets_for(self, subject: str) -> list[str]:
        urls = []
        for pattern, targets in self.routes:
            if subject_matches(pattern, subject):
                urls.extend(url for url in targets if url not in urls)
        return urls

    def publish(self, subject: str, body: bytes, *, message_id: str) -> None:
        for url in self.targets_for(subject):
            self._post(url, subject, body, message_id)

    def _post(self, url, subject, body, message_id) -> None:
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": message_id,
            "X-Message-Subject": subject,
            "User-Agent": USER_AGENT,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response.read()
        except urllib.error.HTTPError as error:
            detail = f"POST {url} -> HTTP {error.code}"
            if error.code >= 500 or error.code in TRANSIENT_STATUS:
                raise TransientPublishError(detail) from error
            raise HttpRejected(detail) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise TransientPublishError(f"POST {url} -> {error!r}") from error
