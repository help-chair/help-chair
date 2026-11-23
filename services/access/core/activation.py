"""Activación de cuentas y alta del administrador inicial.

Implementa `/api/access/v1/activate` y `/internal/v1/bootstrap-admin` del
contrato `contracts/access/openapi.yaml`.

Las dos trabajan sobre el mismo mecanismo: una cuenta nace en estado `invitado`
y sin contraseña, y se activa con un token de un solo uso que caduca. Del token
solo se guarda el hash (ver `ActivationToken`).

`/internal/v1` **no se expone en el ingress**: lo llama el aprovisionador desde
dentro del stack, autenticándose con `PROVISIONER_TOKEN`, que no es un JWT.
"""

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivationToken, EstadoUsuario, Rol

Usuario = get_user_model()


class TokenDeActivacionInvalido(ValidationError):
    """400 del contrato: el token no existe, ya se usó o caducó.

    Los tres casos responden lo mismo a propósito: distinguirlos le diría a
    quien prueba enlaces al azar cuáles existieron alguna vez.
    """

    default_detail = "El enlace de activación es inválido, ya se usó o expiró."
    default_code = "token_invalido"


class YaHayAdministrador(APIException):
    """409 del contrato: el aprovisionador reintentó un alta que ya ocurrió."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "administrador_existente"
    default_detail = "Esta empresa ya tiene un administrador."


class CatalogoDeRolesVacio(APIException):
    """El stack se levantó sin correr `make seed`; no es culpa de quien llama."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "catalogo_incompleto"
    default_detail = "El catálogo de roles no está cargado en este stack. Corre `manage.py seed`."


class DatosInvalidos(ValidationError):
    """422: el contrato lo pide así para el alta del administrador."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


# --- Serializers -------------------------------------------------------------


class ActivacionSerializer(serializers.Serializer):
    """Esquema `ActivacionCuenta` del contrato."""

    token = serializers.CharField()
    password = serializers.CharField(
        min_length=settings.LONGITUD_MINIMA_CONTRASENA,
        max_length=settings.LONGITUD_MAXIMA_CONTRASENA,
        write_only=True,
        trim_whitespace=False,
    )


class BootstrapAdminSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    correo = serializers.EmailField()


class AdminCreadoSerializer(serializers.Serializer):
    """Esquema `AdminCreado`: el token en claro se entrega una sola vez."""

    usuario_id = serializers.UUIDField()
    token_activacion = serializers.CharField()
    expira_en = serializers.DateTimeField()


# --- /api/access/v1/activate -------------------------------------------------


@extend_schema(
    tags=["cuenta"],
    operation_id="activateAccount",
    summary="Define la contraseña con el enlace de activación",
    description=(
        "Lo usa `/activar?token=…` en el frontend. El token es de un solo uso y "
        "expira; sirve para el administrador inicial y para los invitados."
    ),
    request=ActivacionSerializer,
    responses={204: None},
    auth=[],
)
class ActivateView(APIView):
    """`POST /activate`: público, porque quien lo llama todavía no tiene sesión."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        cuerpo = ActivacionSerializer(data=request.data)
        cuerpo.is_valid(raise_exception=True)

        registro = ActivationToken.objects.filter(
            token_hash=ActivationToken.hash_of(cuerpo.validated_data["token"])
        ).first()
        if registro is None or not registro.is_usable:
            raise TokenDeActivacionInvalido()

        with transaction.atomic():
            usuario = registro.user
            usuario.set_password(cuerpo.validated_data["password"])
            usuario.estado = EstadoUsuario.ACTIVO
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            usuario.save(
                update_fields=["password", "estado", "intentos_fallidos", "bloqueado_hasta"]
            )
            registro.consume()

        return Response(status=status.HTTP_204_NO_CONTENT)


# --- /internal/v1/bootstrap-admin --------------------------------------------


@extend_schema(
    tags=["interno"],
    operation_id="bootstrapAdmin",
    summary="Crea al administrador inicial de la empresa, sin contraseña",
    description=(
        "Lo llama el aprovisionador justo después de crear el stack. No se expone "
        "en el ingress. Si ya existe un administrador responde 409 y no crea nada."
    ),
    request=BootstrapAdminSerializer,
    responses={201: AdminCreadoSerializer},
    auth=[],
)
class BootstrapAdminView(APIView):
    """`POST /internal/v1/bootstrap-admin`, autenticado con `PROVISIONER_TOKEN`.

    No usa JWT: quien llama es el aprovisionador, que todavía no tiene usuarios
    con los que iniciar sesión.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request) -> str:
        """Sin esto DRF degrada el 401 a 403.

        DRF solo responde 401 si la vista sabe decir *cómo* autenticarse, y esa
        cabecera la aporta el autenticador. Como aquí no hay ninguno (el token
        del aprovisionador no es JWT), hay que declararla a mano o el contrato
        se incumple: pide 401, no 403.
        """
        return 'Bearer realm="internal"'

    def post(self, request):
        self._exigir_token_del_aprovisionador(request)

        cuerpo = BootstrapAdminSerializer(data=request.data)
        if not cuerpo.is_valid():
            raise DatosInvalidos(cuerpo.errors)

        if Usuario.objects.filter(rol_id=Rol.ADMINISTRADOR).exists():
            raise YaHayAdministrador()

        rol = Rol.objects.filter(pk=Rol.ADMINISTRADOR).first()
        if rol is None:
            raise CatalogoDeRolesVacio()

        correo = Usuario.objects.normalize_email(cuerpo.validated_data["correo"])
        if Usuario.objects.filter(correo__iexact=correo).exists():
            raise YaHayAdministrador()

        with transaction.atomic():
            # Sin contraseña: el manager lo deja en estado `invitado`.
            usuario = Usuario.objects.create_user(
                correo=correo, nombre=cuerpo.validated_data["nombre"], rol=rol
            )
            registro, token_en_claro = ActivationToken.issue(
                usuario, settings.ACTIVACION_VIGENCIA_HORAS
            )

        return Response(
            {
                "usuario_id": str(usuario.id),
                "token_activacion": token_en_claro,
                "expira_en": registro.expires_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _exigir_token_del_aprovisionador(request) -> None:
        """401 si falta el token o no coincide.

        Si `PROVISIONER_TOKEN` viene vacío el endpoint queda cerrado: es más
        seguro que un stack mal configurado no acepte a nadie, a que acepte a
        cualquiera.
        """
        esperado = settings.PROVISIONER_TOKEN
        cabecera = request.headers.get("Authorization", "")
        recibido = cabecera[7:] if cabecera.startswith("Bearer ") else ""
        if not esperado or not recibido or not secrets.compare_digest(recibido, esperado):
            raise AuthenticationFailed("Token del aprovisionador ausente o incorrecto.")
