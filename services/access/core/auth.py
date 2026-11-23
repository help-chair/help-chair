"""Autenticación del servicio access: login con JWT y claims propios.

El token lleva lo que declara ``contracts/access/openapi.yaml``: ``sub``,
``empresa``, ``rol``, ``permisos``, ``iat``, ``exp`` e ``iss``.

La **respuesta** usa los nombres del contrato (``acceso``, ``refresco``,
``token_tipo``, ``expira_en`` y ``usuario``), que son los que ya consume
``frontend/src/api/access.ts``. SimpleJWT devolvería ``access`` y ``refresh``
en inglés por su cuenta, así que las dos vistas traducen antes de responder.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings as ajustes_jwt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import events
from .errors import ErrorSerializer
from .models import EstadoUsuario, Rol

TOKEN_TIPO = "Bearer"


class CuentaNoActivada(APIException):
    """403 del contrato: la cuenta existe pero sigue en estado ``invitado``."""

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "cuenta_no_activada"
    default_detail = (
        "La cuenta existe pero todavía no se activa. Usa el enlace de activación "
        "que llegó por correo."
    )


class CuentaBloqueada(APIException):
    """423 del contrato: bloqueada por intentos fallidos."""

    status_code = status.HTTP_423_LOCKED
    default_code = "cuenta_bloqueada"
    default_detail = (
        "La cuenta está bloqueada por intentos fallidos. Pídele a un administrador "
        "que la desbloquee."
    )


def rol_de(usuario) -> str:
    """Identificador del rol que va en el token.

    Un usuario sin rol asignado se trata como usuario final, que es el rol con
    menos permisos.
    """
    return str(getattr(usuario, "rol_id", None) or Rol.USUARIO_FINAL)


def permisos_de(usuario) -> list[str]:
    """Permisos efectivos del usuario. El frontend dibuja la navegación con esto."""
    return list(getattr(usuario, "permisos", []) or [])


def onboarding_de(usuario) -> bool:
    """``onboarding_completed`` vive en el perfil (D-25); sin perfil todavía es falso."""
    perfil = getattr(usuario, "perfil", None)
    return bool(getattr(perfil, "onboarding_completado", False))


def usuario_a_dict(usuario) -> dict:
    """Esquema ``Usuario`` del contrato: lo que ven las listas de administración."""
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": rol_de(usuario),
        "departamento": usuario.departamento.nombre if usuario.departamento_id else None,
        "estado": usuario.estado,
        "ultimo_acceso": usuario.last_login.isoformat() if usuario.last_login else None,
        "creado_en": usuario.date_joined.isoformat(),
    }


def usuario_actual(usuario) -> dict:
    """Esquema ``UsuarioActual``: el ``Usuario`` del contrato más permisos y onboarding.

    Lo devuelven el login, el refresco y ``/me``; ``/usuarios`` devuelve solo la
    parte de ``Usuario``, por eso las dos formas salen de la misma función.
    """
    return usuario_a_dict(usuario) | {
        "permisos": permisos_de(usuario),
        "onboarding_completed": onboarding_de(usuario),
    }


def construir_sesion(usuario, acceso: str, refresco: str) -> dict:
    """Esquema ``Sesion`` del contrato."""
    return {
        "acceso": acceso,
        "refresco": refresco,
        "token_tipo": TOKEN_TIPO,
        "expira_en": int(ajustes_jwt.ACCESS_TOKEN_LIFETIME.total_seconds()),
        "usuario": usuario_actual(usuario),
    }


class UsuarioActualSerializer(serializers.Serializer):
    """Solo documenta la respuesta; la sesión se arma en ``usuario_actual``."""

    id = serializers.UUIDField()
    nombre = serializers.CharField()
    correo = serializers.EmailField()
    rol = serializers.CharField()
    departamento = serializers.CharField(allow_null=True)
    estado = serializers.CharField()
    ultimo_acceso = serializers.DateTimeField(allow_null=True)
    creado_en = serializers.DateTimeField()
    permisos = serializers.ListField(child=serializers.CharField())
    onboarding_completed = serializers.BooleanField()


class SesionSerializer(serializers.Serializer):
    acceso = serializers.CharField()
    refresco = serializers.CharField()
    token_tipo = serializers.CharField()
    expira_en = serializers.IntegerField()
    usuario = UsuarioActualSerializer()


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
        correo = attrs.get(self.username_field, "")
        self._revisar_estado(correo)
        try:
            datos = super().validate(attrs)
        except AuthenticationFailed:
            self._contar_intento_fallido(correo)
            raise
        self.user.registrar_acceso()
        events.login_exitoso(self.user, rol_de(self.user), self.context.get("request"))
        return construir_sesion(self.user, datos["access"], datos["refresh"])

    def _contar_intento_fallido(self, correo: str) -> None:
        """Suma el intento fallido, lo reporta a Eventos y bloquea al llegar al límite.

        Si el bloqueo ocurre justo en este intento, la respuesta cambia de 401 a
        423, para que el frontend pueda decir por qué dejó de servir la contraseña
        en lugar de repetir «credenciales incorrectas».

        Solo se cuentan los intentos contra una cuenta activa: un correo que no
        existe no incrementa ningún contador, y uno invitado o suspendido ya se
        rechazó antes. El **evento** sí se emite en los dos casos: una ráfaga
        contra correos inventados es justo lo que Eventos necesita ver.
        """
        peticion = self.context.get("request")
        usuario = get_user_model().objects.filter(correo__iexact=correo).first()
        if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
            events.login_fallido(correo, 1, peticion)
            return

        bloqueada = usuario.registrar_intento_fallido(settings.INTENTOS_ANTES_DE_BLOQUEAR)
        events.login_fallido(correo, usuario.intentos_fallidos, peticion)
        if bloqueada:
            events.cuenta_bloqueada(usuario, usuario.intentos_fallidos)
            raise CuentaBloqueada()

    @staticmethod
    def _revisar_estado(correo: str) -> None:
        """Separa «sin activar» y «bloqueada» de unas credenciales incorrectas.

        El contrato lo pide así (403 y 423) porque el frontend muestra un mensaje
        distinto en cada caso. Es una concesión consciente: delata que el correo
        existe. Una contraseña incorrecta sigue devolviendo 401 sin revelar si el
        correo está registrado.
        """
        usuario = get_user_model().objects.filter(correo__iexact=correo).first()
        if usuario is None:
            return
        if usuario.estado == EstadoUsuario.INVITADO:
            raise CuentaNoActivada()
        if usuario.estado == EstadoUsuario.BLOQUEADO:
            raise CuentaBloqueada()


class RefrescoSerializer(serializers.Serializer):
    """El contrato llama ``refresco`` al campo que SimpleJWT llama ``refresh``.

    Devuelve la sesión completa, no solo el token nuevo, porque el frontend
    espera el mismo esquema ``Sesion`` que en el login.
    """

    refresco = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            refresco = RefreshToken(attrs["refresco"])
        except TokenError as error:
            raise InvalidToken(str(error)) from error

        usuario = self._usuario_de(refresco)
        acceso = refresco.access_token
        # Se recalculan por si el rol o los permisos cambiaron desde el login.
        acceso["empresa"] = settings.EMPRESA_ID
        acceso["rol"] = rol_de(usuario)
        acceso["permisos"] = permisos_de(usuario)

        # El refresco se devuelve tal cual: en la v0 no hay rotación todavía.
        return construir_sesion(usuario, str(acceso), attrs["refresco"])

    @staticmethod
    def _usuario_de(refresco):
        identificador = refresco.payload.get(ajustes_jwt.USER_ID_CLAIM)
        usuario = get_user_model().objects.filter(pk=identificador).first()
        if usuario is None or not usuario.is_active:
            raise InvalidToken("El token de refresco ya no corresponde a una cuenta activa.")
        return usuario


@extend_schema(
    tags=["auth"],
    summary="Inicia sesión",
    description=(
        "Valida las credenciales y entrega la sesión: token de acceso, token de "
        "refresco y el usuario con sus permisos. El de acceso lleva los claims "
        "`empresa`, `rol` y `permisos`. Solo entran los usuarios en estado `activo`."
    ),
    responses={
        200: SesionSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        403: ErrorSerializer,
        423: ErrorSerializer,
    },
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


@extend_schema(
    tags=["auth"],
    summary="Renueva la sesión",
    description="Entrega una sesión nueva a partir de un token de refresco válido.",
    request=RefrescoSerializer,
    responses={
        200: SesionSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
    },
)
class RefreshView(TokenRefreshView):
    serializer_class = RefrescoSerializer


class CierreDeSesionSerializer(serializers.Serializer):
    """Cuerpo de `POST /logout`: el refresco que se quiere revocar."""

    refresco = serializers.CharField(write_only=True)


@extend_schema(
    tags=["autenticacion"],
    operation_id="logout",
    summary="Cierra la sesión y revoca el token de refresco",
    description=(
        "Manda a la lista negra el token de refresco. Responde 204 aunque el token "
        "ya no sirviera: si respondiera distinto, serviría para averiguar qué "
        "refrescos siguen vivos."
    ),
    request=CierreDeSesionSerializer,
    responses={204: None},
)
class LogoutView(APIView):
    """`POST /logout`.

    El token de **acceso** no se revoca: vive 15 minutos y es de firma, no de
    estado. Lo que se corta es la capacidad de pedir uno nuevo.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        cuerpo = CierreDeSesionSerializer(data=request.data)
        cuerpo.is_valid(raise_exception=True)
        try:
            RefreshToken(cuerpo.validated_data["refresco"]).blacklist()
        except TokenError:
            # Token inválido, expirado o ya revocado: la sesión igual queda cerrada.
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)
