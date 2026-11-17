"""Autenticación del servicio access: login con JWT y claims propios.

El token lleva lo que declara ``contracts/access/openapi.yaml``: ``sub``,
``empresa``, ``rol``, ``permisos``, ``iat``, ``exp`` e ``iss``.
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Rol


def rol_de(usuario) -> str:
    """Identificador del rol que va en el token.

    Un usuario sin rol asignado se trata como usuario final, que es el rol con
    menos permisos.
    """
    return str(getattr(usuario, "rol_id", None) or Rol.USUARIO_FINAL)


def permisos_de(usuario) -> list[str]:
    """Permisos efectivos del usuario. El frontend dibuja la navegación con esto."""
    return list(getattr(usuario, "permisos", []) or [])


class LoginSerializer(TokenObtainPairSerializer):
    """Agrega al token los claims de empresa, rol y permisos.

    La expiración (``exp``), la emisión (``iat``) y el emisor (``iss``) los
    escribe SimpleJWT por su cuenta.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["empresa"] = settings.EMPRESA_ID
        token["rol"] = rol_de(user)
        token["permisos"] = permisos_de(user)
        return token

    def validate(self, attrs):
        datos = super().validate(attrs)
        self.user.registrar_acceso()
        return datos


@extend_schema(
    tags=["auth"],
    summary="Inicia sesión",
    description=(
        "Valida las credenciales y entrega un token de acceso y uno de "
        "refresco. El de acceso lleva los claims `empresa`, `rol` y `permisos`. "
        "Solo entran los usuarios en estado `activo`."
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
