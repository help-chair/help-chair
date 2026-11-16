"""Autenticación del servicio access: login con JWT y claims propios.

El login trabaja sobre el modelo de usuario activo (``get_user_model``). Cuando
el equipo defina su propio ``AUTH_USER_MODEL`` (por ejemplo con el correo como
identificador), este código sigue funcionando sin cambios.
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def rol_de(usuario) -> str:
    """Devuelve el rol del usuario para ponerlo en el token.

    Mientras el modelo Rol/Perfil no exista, se deduce de los permisos de
    Django. Cuando exista, esta función lo lee de ``usuario.perfil.rol`` sin
    que haya que tocar nada más.
    """
    perfil = getattr(usuario, "perfil", None)
    rol = getattr(perfil, "rol", None)
    if rol is not None:
        return str(rol)
    if usuario.is_superuser:
        return "administrador"
    if usuario.is_staff:
        return "agente"
    return "usuario"


class LoginSerializer(TokenObtainPairSerializer):
    """Agrega al token los claims que pide el plan: empresa, rol y expiración.

    La expiración (``exp``) la escribe SimpleJWT por su cuenta.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["empresa"] = settings.EMPRESA_ID
        token["rol"] = rol_de(user)
        return token


@extend_schema(
    tags=["auth"],
    summary="Inicia sesión",
    description=(
        "Valida las credenciales y entrega un token de acceso y uno de "
        "refresco. El token de acceso lleva los claims `empresa`, `rol` y `exp`."
    ),
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


@extend_schema(
    tags=["auth"],
    summary="Renueva el token de acceso",
    description="Entrega un token de acceso nuevo a partir de uno de refresco válido.",
)
class RefreshView(TokenRefreshView):
    pass
