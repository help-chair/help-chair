"""Manda al broker los eventos que esperan en la bandeja de salida.

Se corre periódicamente, desde cron en local o desde un CronJob en el clúster:

    python manage.py publicar_eventos

El inicio de sesión nunca depende de esto: escribe su evento en la misma
transacción y sigue. Si el broker está caído, los eventos se quedan pendientes
y el siguiente pase los manda.

Publica con NATS a secas y confirma con `flush` antes de marcar cada mensaje:
eso asegura que el servidor lo recibió.

Falta el paso a `js.publish`, que además confirmaría que el mensaje quedó
almacenado, y no se puede dar todavía: el único stream de JetStream que existe
es `EVENTS`, y cubre `events.>`, no `access.>` (ver `services/events/docs/outbox.md`).
Mientras no haya un stream que cubra nuestros subjects, un evento publicado sin
nadie escuchando se descarta. Hay que acordar con Eventos de quién es ese stream
antes de cambiar esta línea.
"""

from __future__ import annotations

import asyncio

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.outbox import LOTE_POR_OMISION, publicar_pendientes

ESPERA_SEGUNDOS = 5


class PublicadorNats:
    """Conexión al broker, usable como función: `publicador(subject, cuerpo)`."""

    def __init__(self, url: str, espera: float = ESPERA_SEGUNDOS):
        self.url = url
        self.espera = espera
        self._bucle = None
        self._conexion = None

    def __enter__(self) -> PublicadorNats:
        import nats  # se importa aquí para que las pruebas no necesiten el paquete

        self._bucle = asyncio.new_event_loop()
        self._conexion = self._bucle.run_until_complete(
            nats.connect(self.url, connect_timeout=self.espera, max_reconnect_attempts=1)
        )
        return self

    def __call__(self, subject: str, cuerpo: bytes, cabeceras: dict[str, str]) -> None:
        async def enviar():
            await self._conexion.publish(subject, cuerpo, headers=cabeceras)
            # `flush` espera la confirmación del servidor; `publish` por sí solo
            # no garantiza nada y marcaríamos como publicado algo que se perdió.
            await self._conexion.flush(timeout=self.espera)

        self._bucle.run_until_complete(enviar())

    def __exit__(self, *_) -> None:
        if self._conexion is not None:
            self._bucle.run_until_complete(self._conexion.close())
        if self._bucle is not None:
            self._bucle.close()


class Command(BaseCommand):
    help = "Publica en el broker los eventos pendientes de la bandeja de salida."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lote",
            type=int,
            default=LOTE_POR_OMISION,
            help=f"Máximo de mensajes por pase (por omisión {LOTE_POR_OMISION}).",
        )
        parser.add_argument(
            "--url",
            default=None,
            help="URL del broker; por omisión, la de BROKER_URL.",
        )

    def handle(self, *args, **opciones):
        url = opciones["url"] or settings.BROKER_URL
        if not url:
            raise CommandError("Falta BROKER_URL. Ver .env.example.")

        try:
            with PublicadorNats(url) as publicar:
                publicados, fallidos = publicar_pendientes(publicar, opciones["lote"])
        except CommandError:
            raise
        except Exception as error:
            raise CommandError(f"No se pudo publicar en {url}: {error}") from error

        if publicados:
            self.stdout.write(self.style.SUCCESS(f"Publicados {publicados} evento(s)."))
        else:
            self.stdout.write("Sin eventos pendientes.")
        if fallidos:
            raise CommandError(
                "El broker dejó de responder a media tanda; los eventos sin publicar "
                "siguen pendientes y el próximo pase los reintenta."
            )
