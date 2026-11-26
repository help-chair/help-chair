"""Publicación de mensajes de Eventos al broker con el patrón *outbox*.

- messages: escribe los mensajes en la transacción del cambio y arma el sobre común.
- relay: publica los pendientes con reintentos (interfaz `Publisher`).
- jetstream: publicador de NATS JetStream (por omisión).
- http: plan B, entrega por REST con la misma interfaz (`OUTBOX_TRANSPORT=http`).
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .messages import (
    ROUTED,
    STATE_CHANGED,
    encode,
    enqueue,
    enqueue_routed,
    enqueue_state_changed,
    envelope,
)
from .relay import Publisher, RelayResult, TransientPublishError, drain, publish_pending


def get_publisher(url=None):
    """Publicador según OUTBOX_TRANSPORT: `jetstream` (por omisión) o `http` (plan B).

    No conecta: eso pasa al entrar al contexto (`with get_publisher() as publisher`). Lanza
    ImproperlyConfigured si falta configuración.
    """
    transport = settings.OUTBOX_TRANSPORT
    if transport == "http":
        from .http import HttpPublisher

        return HttpPublisher.from_settings()
    if transport == "jetstream":
        url = url or settings.BROKER_URL
        if not url:
            raise ImproperlyConfigured("Falta BROKER_URL (ver .env.example).")
        if not url.startswith(("nats://", "tls://")):
            raise ImproperlyConfigured(f"BROKER_URL debe ser nats:// o tls://, no {url!r}")
        from .jetstream import JetStreamPublisher

        return JetStreamPublisher(url)
    raise ImproperlyConfigured(f"OUTBOX_TRANSPORT desconocido: {transport!r} (jetstream o http)")


__all__ = [
    "ROUTED",
    "STATE_CHANGED",
    "Publisher",
    "RelayResult",
    "TransientPublishError",
    "drain",
    "encode",
    "enqueue",
    "enqueue_routed",
    "enqueue_state_changed",
    "envelope",
    "get_publisher",
    "publish_pending",
]
