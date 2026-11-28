import logging
import signal
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from events.services.dispatch import retry_pending

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Entrega las salidas pendientes a los servicios destino (una vez o en bucle)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--loop", action="store_true", help="Corre hasta recibir SIGTERM")
        parser.add_argument("--interval", type=float, default=5.0)

    def handle(self, *args, **options):
        if not options["loop"]:
            self.stdout.write(f"Reintentadas: {retry_pending(options['limit'])}")
            return
        stop = False

        def request_stop(*_):
            nonlocal stop
            stop = True

        signal.signal(signal.SIGTERM, request_stop)
        signal.signal(signal.SIGINT, request_stop)
        while not stop:
            close_old_connections()
            try:
                handled = retry_pending(options["limit"])
            except Exception:  # BD aún sin migrar, caída temporal, etc.: se vuelve a intentar
                logger.exception("retry_routing_failed")
                handled = 0
            if handled == 0:
                time.sleep(options["interval"])
