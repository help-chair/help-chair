"""Consume mensajes durables de Accesos desde NATS JetStream."""

import asyncio
import json
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from events.services.access_ingestion import InvalidAccessMessage, process_access_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consume eventos de seguridad de Accesos desde NATS JetStream."

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=None)
        parser.add_argument("--timeout", type=float, default=None)

    def handle(self, *args, **options):
        if not settings.BROKER_URL:
            raise CommandError("Define BROKER_URL para consumir mensajes de Accesos.")
        batch_size = options["batch"] or settings.ACCESS_EVENTS_BATCH_SIZE
        timeout = options["timeout"] or settings.ACCESS_EVENTS_FETCH_TIMEOUT_SECONDS
        if batch_size < 1 or timeout <= 0:
            raise CommandError("batch debe ser positivo y timeout debe ser mayor que cero.")
        asyncio.run(self._consume(batch_size=batch_size, timeout=timeout))

    async def _consume(self, *, batch_size, timeout):
        import nats
        from nats.errors import TimeoutError as NatsTimeoutError

        connection = await nats.connect(servers=[settings.BROKER_URL])
        try:
            subscription = await connection.jetstream().pull_subscribe(
                settings.ACCESS_EVENTS_SUBJECT,
                durable=settings.ACCESS_EVENTS_DURABLE,
                stream=settings.ACCESS_EVENTS_STREAM,
            )
            logger.info(
                "access_consumer_started",
                extra={
                    "stream": settings.ACCESS_EVENTS_STREAM,
                    "subject": settings.ACCESS_EVENTS_SUBJECT,
                    "durable": settings.ACCESS_EVENTS_DURABLE,
                },
            )
            while True:
                try:
                    messages = await subscription.fetch(batch=batch_size, timeout=timeout)
                except NatsTimeoutError:
                    continue
                for message in messages:
                    try:
                        envelope = json.loads(message.data)
                        result = await sync_to_async(process_access_message, thread_sensitive=True)(
                            envelope
                        )
                    except (
                        UnicodeDecodeError,
                        json.JSONDecodeError,
                        InvalidAccessMessage,
                    ) as error:
                        logger.error(
                            "access_message_rejected",
                            extra={"error": str(error)},
                        )
                        await message.term()
                        continue
                    await message.ack()
                    logger.debug(
                        "access_message_acknowledged",
                        extra={
                            "duplicate": result.duplicate,
                            "event_id": str(result.event.id) if result.event else None,
                        },
                    )
        finally:
            await connection.close()
