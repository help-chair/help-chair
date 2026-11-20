import asyncio
import json
import logging
import signal

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from peticiones.consumers import EventoInvalidoError, procesar_evento_enrutado

logger = logging.getLogger(__name__)


async def manejar_mensaje_crudo(raw_data: bytes) -> None:
    try:
        payload = json.loads(raw_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("Mensaje descartado por JSON inválido: %s", exc)
        return

    try:
        await sync_to_async(procesar_evento_enrutado, thread_sensitive=True)(payload)
    except EventoInvalidoError as exc:
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

        asyncio.run(self._escuchar(nats, broker_url, subject))

    async def _escuchar(self, nats_module, broker_url: str, subject: str) -> None:
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                pass

        nc = await nats_module.connect(broker_url)
        logger.info("Conectado a NATS en %s escuchando '%s'", broker_url, subject)

        async def _callback(msg):
            await manejar_mensaje_crudo(msg.data)

        sub = await nc.subscribe(subject, cb=_callback)
        try:
            await stop_event.wait()
        finally:
            await sub.unsubscribe()
            await nc.drain()
            logger.info("Consumidor de eventos detenido limpiamente")