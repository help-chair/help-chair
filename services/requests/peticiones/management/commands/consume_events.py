import asyncio
import json
import logging
import signal

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from peticiones.consumers import InvalidEventError, process_routed_event

logger = logging.getLogger(__name__)


async def handle_raw_message(raw_data: bytes) -> None:
    try:
        envelope = json.loads(raw_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("Mensaje descartado por JSON inválido: %s", exc)
        return

    try:
        await sync_to_async(process_routed_event, thread_sensitive=True)(envelope)
    except InvalidEventError as exc:
        logger.warning("Mensaje descartado por esquema inválido: %s", exc)
    except Exception:
        logger.exception("Error inesperado procesando evento desde el broker")
        raise


class Command(BaseCommand):
    help = "Consume eventos enrutados desde NATS y crea peticiones automáticamente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--broker-url",
            default=settings.BROKER_URL,
            help="URL de conexión al broker NATS (por defecto BROKER_URL).",
        )
        parser.add_argument(
            "--subject",
            default=settings.BROKER_EVENTS_SUBJECT,
            help="Subject de NATS a escuchar (por defecto BROKER_EVENTS_SUBJECT).",
        )

    def handle(self, *args, **options):
        broker_url = options["broker_url"]
        subject = options["subject"]

        if not broker_url:
            raise CommandError(
                "Define BROKER_URL en el entorno o pásalo con --broker-url."
            )

        try:
            import nats
        except ImportError as exc:
            raise CommandError(
                "Falta la dependencia 'nats-py'. Instálala con `uv add nats-py`."
            ) from exc

        asyncio.run(self._listen(nats, broker_url, subject))

    async def _listen(self, nats_module, broker_url: str, subject: str) -> None:
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                pass

        connection = await nats_module.connect(broker_url)
        logger.info("Conectado a NATS en %s escuchando '%s'", broker_url, subject)

        async def _callback(message):
            await handle_raw_message(message.data)

        subscription = await connection.subscribe(subject, cb=_callback)
        try:
            await stop_event.wait()
        finally:
            await subscription.unsubscribe()
            await connection.drain()
            logger.info("Consumidor de eventos detenido limpiamente")