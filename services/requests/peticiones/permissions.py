"""Permisos de Peticiones con el JWT que emite Accesos.

Como en Accesos (``services/access/core/permissions.py``), se pregunta por
**permiso** y no por rol: los permisos viajan en el claim ``permisos`` del token,
así que agregar un rol nuevo no obliga a tocar este servicio.

- ``tickets:ver``: todos los roles. Quien no tiene ``tickets:atender`` (el usuario
  final) solo ve y gestiona **sus** peticiones.
- ``tickets:atender``: agentes y administradores; asignan, cambian estado y editan.
- ``empresa:configurar``: administradores; editan el catálogo y aprueban o rechazan
  cambios (hasta que el onboarding defina un aprobador, fase 4).

Sin ``JWT_AUTH_ENABLED`` (pruebas aisladas y Schemathesis) no se exige token.
"""

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication

TICKETS_VIEW = "tickets:ver"
TICKETS_ATTEND = "tickets:atender"
COMPANY_CONFIGURE = "empresa:configurar"

# Cambios de estado que el solicitante puede hacer sobre su propia petición:
# cancelarla, cerrarla al calificar la atención o reabrirla si no quedó resuelta.
REQUESTER_STATUS_CHANGES = {"cancelado", "cerrado", "reabierto"}

# Acciones de la API de peticiones reservadas a quien atiende.
ATTEND_ACTIONS = {"assign", "update", "partial_update", "destroy"}
APPROVAL_ACTIONS = {"approve", "reject"}


class OptionalAccessJWTAuthentication(JWTStatelessUserAuthentication):
    """Valida el JWT de Accesos únicamente cuando `JWT_AUTH_ENABLED=True`."""

    def authenticate(self, request):
        if not jwt_enabled():
            return None
        return super().authenticate(request)


class OptionalAccessJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "peticiones.permissions.OptionalAccessJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


def jwt_enabled() -> bool:
    return getattr(settings, "JWT_AUTH_ENABLED", False)


def token_permissions(request) -> set[str]:
    """Permisos del claim `permisos`; sin claim, ninguno (falla cerrado)."""
    token = getattr(request, "auth", None)
    try:
        permissions = token["permisos"] if token is not None else None
    except (KeyError, TypeError):
        permissions = None
    if not isinstance(permissions, list | tuple | set):
        return set()
    return {str(permission) for permission in permissions}


def token_user_id(request) -> str:
    """Id (UUID) del usuario en Accesos, tomado del claim `sub`."""
    user = getattr(request, "user", None)
    return str(getattr(user, "id", "") or "")


def can_attend(request) -> bool:
    """True si quien llama atiende peticiones (o si el JWT está desactivado)."""
    return not jwt_enabled() or TICKETS_ATTEND in token_permissions(request)


class RequestsServicePermission(BasePermission):
    """Exige un JWT de Accesos con el permiso que pide cada operación."""

    message = "Se requiere un token JWT válido emitido por Accesos."

    def has_permission(self, request, view) -> bool:
        if not jwt_enabled():
            return True

        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False

        permissions = token_permissions(request)
        if TICKETS_VIEW not in permissions:
            self.message = "Tu rol no tiene permiso para usar Peticiones."
            return False

        if view.__class__.__name__ == "CatalogItemViewSet":
            if request.method in SAFE_METHODS:
                return True
            self.message = "Solo un administrador puede editar el catálogo."
            return COMPANY_CONFIGURE in permissions

        action_name = getattr(view, "action", None)
        if action_name in APPROVAL_ACTIONS:
            self.message = "Solo un administrador puede aprobar o rechazar cambios."
            return COMPANY_CONFIGURE in permissions
        if action_name in ATTEND_ACTIONS:
            self.message = "Solo soporte puede asignar, editar o borrar peticiones."
            return TICKETS_ATTEND in permissions

        # Listar, consultar, crear y cambiar estado: el usuario final solo sobre las suyas
        # (lo limitan get_queryset y has_object_permission).
        return True

    def has_object_permission(self, request, view, obj) -> bool:
        if can_attend(request):
            return True
        requester_id = getattr(obj, "requester_id", None)
        if requester_id is None:  # p. ej. un servicio del catálogo
            return True
        self.message = "Solo puedes ver y gestionar tus propias peticiones."
        return requester_id == token_user_id(request)
