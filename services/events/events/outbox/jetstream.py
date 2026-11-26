"""Publicador de NATS JetStream (broker del stack, ADR-87 / D-19).

Con NATS a secas, un mensaje publicado sin suscriptores conectados se pierde aunque el servidor
lo haya recibido. JetStream lo guarda en un *stream* y lo confirma (`PubAck`) solo después de
almacenarlo: ese es el punto en que el outbox puede marcarlo como publicado.

- **Stream:** `settings.OUTBOX_STREAM` (por omisión `EVENTS`) con los subjects `events.>`. Lo crea
  este publicador si no existe; si ya existe, no se modifica.
- **Idempotencia:** la cabecera `Nats-Msg-Id` lleva el `id` del sobre. Si un reintento repite un
  mensaje dentro de la ventana de duplicados del stream, JetStream lo descarta (`duplicate`).
- `nats` se importa aquí, no a nivel de módulo, para que el resto del servicio no lo necesite.
"""

import asyncio
import logging

from django.conf import settings

from .relay import TransientPublishError

logger = logging.getLogger(__name__)

STREAM_SUBJECTS = ("events.>",)


class BrokerUnavailable(TransientPublishError):
    """No hay conexión con el broker o no tiene JetStream activo."""


class JetStreamPublisher:
    """Conexión a JetStream usable como contexto: `with JetStreamPublisher(url) as p: ...`."""

    def __init__(self, url: str, *, stream=None, timeout=None, max_age_days=None):
        self.url = url
        self.stream = stream or settings.OUTBOX_STREAM
        self.timeout = timeout or settings.OUTBOX_PUBLISH_TIMEOUT_SECONDS
        self.max_age_days = max_age_days or settings.OUTBOX_STREAM_MAX_AGE_DAYS
        self._loop = None
        self._nc = None
        self._js = None

    def _run(self, coroutine):
        return self._loop.run_until_complete(coroutine)

    async def _connect(self):
        import nats

        async def on_error(error):  # nats imprime trazas por omisión; aquí van al log JSON
            logger.debug("outbox_broker_client_error", extra={"error": repr(error)})

        # Ojo: en nats-py, max_reconnect_attempts=0 significa "sin límite" al conectar. Con 1
        # se rinde tras un reintento; wait_for es la red de seguridad para no colgar el proceso.
        return await asyncio.wait_for(
            nats.connect(
                servers=[self.url],
                connect_timeout=self.timeout,
                allow_reconnect=False,
                max_reconnect_attempts=1,
                reconnect_time_wait=0.5,
                error_cb=on_error,
            ),
            timeout=self.timeout * 3,
        )

    def __enter__(self) -> "JetStreamPublisher":
        self._loop = asyncio.new_event_loop()
        try:
            self._nc = self._run(self._connect())
            self._js = self._nc.jetstream(timeout=self.timeout)
            self._run(self._ensure_stream())
        except Exception as error:
            self.close()
            raise BrokerUnavailable(
                f"No se pudo usar JetStream en {self.url}: {error!r}"
            ) from error
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def close(self) -> None:
        if self._nc is not None and not self._nc.is_closed:
            try:
                self._run(self._nc.close())
            except Exception:  # noqa: BLE001 - cerrar no debe tapar el error original
                logger.debug("outbox_broker_close_failed", exc_info=True)
        if self._loop is not None:
            self._loop.close()
        self._nc = self._js = self._loop = None

    async def _ensure_stream(self) -> None:
        from nats.js.errors import NotFoundError

        try:
            await self._js.stream_info(self.stream)
        except NotFoundError:
            await self._js.add_stream(
                name=self.stream,
                subjects=list(STREAM_SUBJECTS),
                max_age=self.max_age_days * 24 * 60 * 60,  # segundos; nats-py lo pasa a ns
            )
            logger.info(
                "outbox_stream_created",
                extra={"stream": self.stream, "subjects": list(STREAM_SUBJECTS)},
            )

    def publish(self, subject: str, body: bytes, *, message_id: str) -> None:
        from nats.errors import BadHeaderError, BadSubjectError, MaxPayloadError
        from nats.errors import Error as NatsError
        from nats.js.errors import APIError, ServerError, ServiceUnavailableError

        try:
            ack = self._run(
                self._js.publish(
                    subject, body, headers={"Nats-Msg-Id": message_id}, timeout=self.timeout
                )
            )
        except (MaxPayloadError, BadSubjectError, BadHeaderError):
            raise  # del mensaje: cuenta para FAILED
        except (ServiceUnavailableError, ServerError) as error:
            raise TransientPublishError(repr(error)) from error
        except APIError:
            raise  # JetStream rechazó el mensaje (p. ej. stream esperado distinto)
        except (TimeoutError, NatsError, OSError) as error:  # asyncio.TimeoutError es TimeoutError
            raise TransientPublishError(repr(error)) from error
        if ack.duplicate:
            logger.info(
                "outbox_duplicate_discarded",
                extra={"message_id": message_id, "stream": ack.stream, "seq": ack.seq},
            )
