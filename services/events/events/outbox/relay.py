"""Segunda mitad del patrón *outbox*: publicar lo que quedó escrito, con reintentos.

`publish_pending` toma los mensajes PENDING cuyo `next_attempt_at` ya llegó, los envuelve en el
sobre común y se los pasa a un `Publisher` (JetStream hoy; REST como plan B, misma interfaz).

Dos tipos de falla:

- **Temporal** (`TransientPublishError`: broker caído, timeout): se corta el pase y el mensaje
  sigue PENDING y vencido. No cuenta para FAILED (una caída larga no es culpa del mensaje) y no
  se reprograma, para que al volver el broker salgan en el mismo orden en que se escribieron.
- **Permanente** (cualquier otra excepción: mensaje demasiado grande, subject inválido...): se
  reprograma con espera exponencial y, al llegar a `max_attempts`, pasa a FAILED. El pase sigue
  con los demás, para que un mensaje defectuoso no frene a todos.

Garantía: *al menos una vez*. Se marca PUBLISHED solo después de la confirmación del broker; si
algo falla entre la confirmación y el guardado, el mensaje se reenvía con el mismo `id`, que el
broker (Nats-Msg-Id) y los consumidores usan para descartar el duplicado.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from ..models import OutboxMessage, OutboxStatus
from .messages import encode, envelope

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 2000


class TransientPublishError(Exception):
    """El broker no está disponible por ahora; el mensaje se reintenta sin penalizarlo."""


class Publisher(Protocol):
    def publish(self, subject: str, body: bytes, *, message_id: str) -> None:
        """Publica y regresa solo cuando el destino confirmó. Si no, lanza una excepción."""


@dataclass
class RelayResult:
    published: int = 0
    retried: int = 0  # fallas permanentes reprogramadas
    failed: int = 0  # mensajes que pasaron a FAILED en este pase
    broker_unavailable: bool = False

    @property
    def processed(self) -> int:
        return self.published + self.retried + self.failed


def backoff_seconds(attempts: int) -> int:
    """Espera antes del siguiente intento: base, 2×base, 4×base... con tope."""
    base = settings.OUTBOX_BACKOFF_BASE_SECONDS
    return min(settings.OUTBOX_BACKOFF_MAX_SECONDS, base * 2 ** max(attempts - 1, 0))


def due_messages(batch_size: int, now):
    queryset = OutboxMessage.objects.filter(
        status=OutboxStatus.PENDING, next_attempt_at__lte=now
    ).order_by("created_at", "id")
    if connection.features.has_select_for_update_skip_locked:
        # Dos publicadores a la vez no toman el mismo mensaje (PostgreSQL). SQLite no lo soporta.
        queryset = queryset.select_for_update(skip_locked=True)
    return queryset[:batch_size]


def _describe(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"[:MAX_ERROR_LENGTH]


def _log_extra(message: OutboxMessage, error: Exception) -> dict:
    return {
        "message_id": str(message.id),
        "message_type": message.message_type,
        "subject": message.subject,
        "attempts": message.attempts,
        "error": _describe(error),
    }


def publish_pending(
    publisher: Publisher, *, batch_size=None, max_attempts=None, now=None
) -> RelayResult:
    """Un pase de publicación (hasta `batch_size` mensajes)."""
    batch_size = batch_size or settings.OUTBOX_BATCH_SIZE
    max_attempts = max_attempts or settings.OUTBOX_MAX_ATTEMPTS
    now = now or timezone.now()
    result = RelayResult()

    with transaction.atomic():
        for message in due_messages(batch_size, now):
            try:
                body = encode(envelope(message, published_at=now))
                publisher.publish(message.subject, body, message_id=str(message.id))
            except TransientPublishError as error:
                message.attempts += 1
                message.last_error = _describe(error)
                message.save(update_fields=["attempts", "last_error"])
                logger.warning("outbox_broker_unavailable", extra=_log_extra(message, error))
                result.broker_unavailable = True
                break
            except Exception as error:  # noqa: BLE001 - cualquier otra falla es del mensaje
                message.attempts += 1
                message.last_error = _describe(error)
                if message.attempts >= max_attempts:
                    message.status = OutboxStatus.FAILED
                    result.failed += 1
                    logger.error("outbox_message_failed", extra=_log_extra(message, error))
                else:
                    message.next_attempt_at = now + timedelta(
                        seconds=backoff_seconds(message.attempts)
                    )
                    result.retried += 1
                    logger.warning("outbox_publish_retry", extra=_log_extra(message, error))
                message.save(update_fields=["attempts", "last_error", "status", "next_attempt_at"])
                continue

            message.status = OutboxStatus.PUBLISHED
            message.published_at = now
            message.attempts += 1
            message.last_error = ""
            message.save(update_fields=["status", "published_at", "attempts", "last_error"])
            result.published += 1

    if result.published:
        logger.info("outbox_published", extra={"count": result.published})
    return result


def drain(publisher: Publisher, *, batch_size=None, max_attempts=None) -> RelayResult:
    """Pases sucesivos hasta que no quede nada vencido o el broker deje de responder."""
    total = RelayResult()
    while True:
        result = publish_pending(publisher, batch_size=batch_size, max_attempts=max_attempts)
        total.published += result.published
        total.retried += result.retried
        total.failed += result.failed
        if result.broker_unavailable:
            total.broker_unavailable = True
            return total
        if result.processed == 0:
            return total
