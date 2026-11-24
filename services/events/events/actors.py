"""Quién hace la petición (se guarda en el historial)."""

from django.conf import settings

ACTOR_HEADER = "X-Actor-Ref"


def get_actor_ref(request) -> str:
    """Referencia del usuario que actúa: el usuario autenticado (`sub` del JWT de Accesos).

    TEMPORAL: mientras no se integre el JWT, con ALLOW_ACTOR_HEADER=True se acepta la
    cabecera X-Actor-Ref. Es falsificable, por eso solo debe usarse en desarrollo y pruebas.
    """
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return str(getattr(user, "pk", "") or "")
    if getattr(settings, "ALLOW_ACTOR_HEADER", False):
        return (request.headers.get(ACTOR_HEADER) or "").strip()[:64]
    return ""
