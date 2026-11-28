"""La otra mitad del patrón outbox: publicar hacia el broker lo que quedó escrito.

`core/events.py` escribe el evento en `OutboxMessage` dentro de la misma
transacción que la operación que lo provocó. Aquí se leen los que siguen sin
publicar, se envuelven en el sobre común y se mandan.

El sobre es `contracts/messages/event-envelope.json`, que define Eventos. El
`id` del mensaje viaja como `id` del sobre y es la clave de idempotencia: si un
pase falla a medias y el siguiente reenvía, el consumidor reconoce el duplicado.

Ese mismo `id` viaja además en la cabecera `Nats-Msg-Id`, que es donde
JetStream y los consumidores de Eventos buscan la clave para descartar
duplicados (ver `services/events/docs/outbox.md`). Dentro del sobre no la
leen, así que mandarla solo ahí no serviría de nada.

**El subject es el propio tipo del evento.** El contrato sugiere
`<origin>.<type>`, y como nuestros tipos ya empiezan con `access.`, usarlos tal
cual evita un `access.access.login.exitoso` redundante. Quien consuma se
suscribe a `access.>`.

Garantía: se marca `published_at` solo después de que el publicador confirmó.
Si el broker no responde, la fila se queda pendiente. Puede haber duplicados,
nunca pérdidas, y de los duplicados se encarga el `id`.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from django.db import connection, transaction
from django.utils import timezone

from .models import OutboxMessage

# Recibe (subject, cuerpo, cabeceras) y lanza una excepción si no pudo publicar.
Publicador = Callable[[str, bytes, dict[str, str]], None]

LOTE_POR_OMISION = 100


def sobre(mensaje: OutboxMessage) -> dict:
    """El mensaje envuelto como pide `contracts/messages/event-envelope.json`."""
    return {
        "id": str(mensaje.id),
        "type": mensaje.type,
        "version": mensaje.version,
        "origin": OutboxMessage.ORIGIN,
        # `timestamp` es cuándo se publica; `occurred_at`, cuándo pasó el hecho.
        "timestamp": timezone.now().isoformat(),
        "occurred_at": mensaje.occurred_at.isoformat(),
        "payload": mensaje.payload,
    }


def cuerpo(mensaje: OutboxMessage) -> bytes:
    return json.dumps(sobre(mensaje), ensure_ascii=False).encode("utf-8")


def cabeceras(mensaje: OutboxMessage) -> dict[str, str]:
    """`Nats-Msg-Id` es la clave de deduplicación que leen JetStream y Eventos."""
    return {"Nats-Msg-Id": str(mensaje.id)}


def pendientes(lote: int):
    """Los mensajes sin publicar, del más viejo al más nuevo."""
    consulta = OutboxMessage.objects.filter(published_at__isnull=True).order_by("created_at")
    if connection.features.has_select_for_update_skip_locked:
        # Deja que dos publicadores corran a la vez sin mandar lo mismo dos veces.
        # SQLite no lo soporta, y en las pruebas corre un solo proceso.
        consulta = consulta.select_for_update(skip_locked=True)
    return consulta[:lote]


def publicar_pendientes(publicador: Publicador, lote: int = LOTE_POR_OMISION) -> tuple[int, int]:
    """Publica hasta `lote` mensajes. Devuelve (publicados, pendientes_por_error).

    En cuanto uno falla se corta el pase: si el broker está caído, insistir con
    los demás solo alarga la espera. Lo que ya se publicó queda marcado.
    """
    publicados = 0
    fallidos = 0
    with transaction.atomic():
        for mensaje in pendientes(lote):
            try:
                publicador(mensaje.type, cuerpo(mensaje), cabeceras(mensaje))
            except Exception:
                fallidos = 1
                break
            mensaje.published_at = timezone.now()
            mensaje.save(update_fields=["published_at"])
            publicados += 1
    return publicados, fallidos
