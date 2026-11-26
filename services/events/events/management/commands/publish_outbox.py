"""Publica en el broker los mensajes pendientes del outbox de Eventos.

    python manage.py publish_outbox            # un pase: publica lo vencido y termina (CronJob)
    python manage.py publish_outbox --loop     # proceso continuo (worker); termina con SIGTERM

Si el broker no responde, los mensajes se quedan PENDING y el siguiente pase los manda: el
registro de eventos nunca depende del broker. Detalle en docs/outbox.md.
"""

import logging
import signal
import threading

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from events.outbox import drain, get_publisher
from events.outbox.relay import TransientPublishError

logger = logging.getLogger("events.outbox")

MAX_RECONNECT_WAIT_SECONDS = 60


class Command(BaseCommand):
    help = "Publica los mensajes pendientes del outbox (JetStream o, plan B, REST)."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Corre continuamente (worker).")
        parser.add_argument(
            "--interval",
            type=float,
            default=None,
            help="Segundos entre pases con --loop (por omisión OUTBOX_POLL_INTERVAL_SECONDS).",
        )
        parser.add_argument("--batch", type=int, default=None, help="Mensajes por pase.")
        parser.add_argument(
            "--max-attempts", type=int, default=None, help="Intentos antes de marcar FAILED."
        )
        parser.add_argument(
            "--url", default=None, help="URL de NATS (por omisión BROKER_URL; solo jetstream)."
        )

    def handle(self, *args, **options):
        url = options["url"]
        try:
            get_publisher(url)  # valida la configuración del transporte; no conecta
        except ImproperlyConfigured as error:
            raise CommandError(f"{error} Los mensajes siguen PENDING.") from error
        relay_options = {"batch_size": options["batch"], "max_attempts": options["max_attempts"]}
        if options["loop"]:
            interval = options["interval"] or settings.OUTBOX_POLL_INTERVAL_SECONDS
            self._loop(url, interval, relay_options)
        else:
            self._once(url, relay_options)

    # --- un pase ----------------------------------------------------------------------
    def _once(self, url, relay_options):
        try:
            with get_publisher(url) as publisher:
                result = drain(publisher, **relay_options)
        except TransientPublishError as error:
            logger.error("outbox_broker_unavailable", extra={"error": str(error)})
            raise CommandError(
                "Destino no disponible (broker o receptor REST); los mensajes siguen "
                f"PENDING. {error}"
            ) from error

        self.stdout.write(
            f"Publicados: {result.published} · reprogramados: {result.retried} · "
            f"fallidos: {result.failed}"
        )
        if result.broker_unavailable:
            raise CommandError(
                "El destino dejó de responder a media tanda; el resto sigue PENDING."
            )

    # --- worker -----------------------------------------------------------------------
    def _loop(self, url, interval, relay_options):
        stop = threading.Event()

        def request_stop(signum, _frame):
            logger.info("outbox_worker_stopping", extra={"signal": signum})
            stop.set()

        for name in ("SIGTERM", "SIGINT"):
            if hasattr(signal, name):
                signal.signal(getattr(signal, name), request_stop)

        logger.info("outbox_worker_started", extra={"interval_seconds": interval})
        failures = 0
        while not stop.is_set():
            try:
                with get_publisher(url) as publisher:
                    failures = 0
                    while not stop.is_set():
                        result = drain(publisher, **relay_options)
                        if result.broker_unavailable:
                            raise TransientPublishError("el broker dejó de responder")
                        stop.wait(interval)
            except TransientPublishError as error:
                failures += 1
                wait = min(MAX_RECONNECT_WAIT_SECONDS, interval * 2 ** (failures - 1))
                logger.warning(
                    "outbox_broker_unavailable",
                    extra={"error": str(error), "retry_in_seconds": wait, "failures": failures},
                )
                stop.wait(wait)
        logger.info("outbox_worker_stopped")
