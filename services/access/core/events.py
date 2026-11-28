"""Eventos de seguridad que access publica hacia el servicio de Eventos.

Los tipos y sus datos están en `contracts/messages/access-eventos-seguridad.yaml`;
el sobre, en `contracts/messages/event-envelope.json`.

No se publica directo al broker: se escribe una fila en `OutboxMessage` dentro
de la misma transacción que el cambio que originó el evento. Así un login nunca
queda registrado sin su evento, ni se emite un evento de algo que se revirtió.
Publicar al broker es trabajo de un proceso aparte: `manage.py publicar_eventos`.
"""

from django.utils import timezone

from .models import OutboxMessage

LOGIN_EXITOSO = "access.login.exitoso"
LOGIN_FALLIDO = "access.login.fallido"
CUENTA_BLOQUEADA = "access.cuenta.bloqueada"


def ip_de(request) -> str | None:
    """IP de quien llama, mirando primero la cabecera que pone el ingress."""
    if request is None:
        return None
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if reenviada:
        # El primer valor es el cliente original; los demás son proxies.
        return reenviada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def registrar(tipo: str, payload: dict) -> OutboxMessage:
    """Deja el evento en la bandeja de salida."""
    return OutboxMessage.objects.create(type=tipo, payload=payload, occurred_at=timezone.now())


def login_exitoso(usuario, rol: str, request=None) -> OutboxMessage:
    return registrar(
        LOGIN_EXITOSO,
        {"usuario_id": str(usuario.id), "rol": rol, "ip": ip_de(request)},
    )


def login_fallido(identificador: str, intentos: int, request=None) -> OutboxMessage:
    """El identificador va tal cual lo escribieron: puede no ser un usuario real."""
    return registrar(
        LOGIN_FALLIDO,
        {"identificador": identificador, "intentos": intentos, "ip": ip_de(request)},
    )


def cuenta_bloqueada(usuario, intentos: int) -> OutboxMessage:
    return registrar(
        CUENTA_BLOQUEADA,
        {
            "usuario_id": str(usuario.id),
            "intentos": intentos,
            "desbloquea_en": (
                usuario.bloqueado_hasta.isoformat() if usuario.bloqueado_hasta else None
            ),
        },
    )
