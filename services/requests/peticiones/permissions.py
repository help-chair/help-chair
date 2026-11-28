from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication

MANAGER_ROLES = {"admin", "supervisor", "agente"}
APPROVER_ROLES = {"admin", "supervisor", "aprobador"}


class OptionalAccessJWTAuthentication(JWTStatelessUserAuthentication):
    """Valida el JWT de Accesos únicamente cuando `JWT_AUTH_ENABLED=True`."""

    def authenticate(self, request):
        if not getattr(settings, "JWT_AUTH_ENABLED", False):
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


def _get_token_role(request) -> str:
    token = getattr(request, "auth", None)
    if token is None:
        return ""
    if hasattr(token, "get"):
        return str(token.get("rol") or token.get("role") or "").strip().lower()
    return ""


class RequestsServicePermission(BasePermission):
    """Permisos de Fase 3 integrados con el JWT emitido por el servicio Accesos.

    - Cuando `JWT_AUTH_ENABLED=False` (tests locales aislados / Schemathesis),
      permite el acceso sin exigir cabecera Bearer.
    - Cuando `JWT_AUTH_ENABLED=True` (testing / producción), exige un JWT válido
      firmado por `help-chair-access` y valida rol para catálogo y aprobaciones.
    """

    message = "Se requiere un token JWT válido emitido por Accesos."

    def has_permission(self, request, view) -> bool:
        if not getattr(settings, "JWT_AUTH_ENABLED", False):
            return True

        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False

        role = _get_token_role(request)
        if not role:
            return True

        view_name = view.__class__.__name__
        action_name = getattr(view, "action", None)

        if view_name == "CatalogItemViewSet" and request.method not in SAFE_METHODS:
            self.message = "Solo administradores o supervisores pueden editar el catálogo."
            return role in MANAGER_ROLES

        if action_name in {"approve", "reject"}:
            self.message = "No tienes rol autorizado para aprobar o rechazar cambios."
            return role in APPROVER_ROLES

        return True
