"""Administración de usuarios: listar, invitar, modificar y desbloquear.

Implementa `/api/access/v1/usuarios`, `/usuarios/{id}` y `/usuarios/{id}/desbloquear`
del contrato `contracts/access/openapi.yaml`. Todo pide `usuarios:administrar`.

**Falta a propósito:** la invitación crea la cuenta en estado `invitado` pero
todavía no manda el correo con el enlace de activación, porque el token vive en
`/activate` y ese endpoint aún no existe. Hasta entonces, un invitado no puede
entrar por sí solo. Ver `docs/ROADMAP.md`, fase 3.
"""

from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import usuario_a_dict
from .models import Departamento, EstadoUsuario, Permiso, Rol
from .permissions import requiere

Usuario = get_user_model()

# El contrato solo deja suspender o reactivar desde aquí; el bloqueo por intentos
# fallidos se levanta con /desbloquear, no cambiando el estado a mano.
ESTADOS_EDITABLES = [EstadoUsuario.ACTIVO, EstadoUsuario.SUSPENDIDO]


class CorreoDuplicado(APIException):
    """409 del contrato: ya hay una cuenta con ese correo."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "correo_duplicado"
    default_detail = "Ya existe un usuario con ese correo."


class DatosInvalidos(ValidationError):
    """422: el contrato lo pide así para la invitación, donde DRF usaría 400."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class SinAdministradores(APIException):
    """403 del contrato: la empresa no puede quedarse sin administrador activo."""

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "sin_administradores"
    default_detail = (
        "La empresa quedaría sin ningún administrador activo. Nombra a otro antes de cambiar este."
    )


# --- Serializers -------------------------------------------------------------


class UsuarioSerializer(serializers.Serializer):
    """Solo documenta la respuesta; el cuerpo se arma en ``usuario_a_dict``."""

    id = serializers.UUIDField()
    nombre = serializers.CharField()
    correo = serializers.EmailField()
    rol = serializers.CharField()
    departamento = serializers.CharField(allow_null=True)
    estado = serializers.CharField()
    ultimo_acceso = serializers.DateTimeField(allow_null=True)
    creado_en = serializers.DateTimeField()


class UsuarioListSerializer(serializers.Serializer):
    resultados = UsuarioSerializer(many=True)


class InvitacionSerializer(serializers.Serializer):
    """Esquema `InvitacionUsuario` del contrato."""

    nombre = serializers.CharField(max_length=120)
    correo = serializers.EmailField()
    rol = serializers.CharField()
    departamento = serializers.CharField(max_length=80, required=False, allow_blank=True)


class ActualizacionSerializer(serializers.Serializer):
    """Esquema `ActualizacionUsuario`: al menos un campo, y solo estos tres."""

    rol = serializers.CharField(required=False)
    departamento = serializers.CharField(max_length=80, required=False, allow_null=True)
    estado = serializers.ChoiceField(choices=ESTADOS_EDITABLES, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Manda al menos un campo que cambiar.")
        return attrs


# --- Ayudantes ---------------------------------------------------------------


def rol_o_error(identificador: str) -> Rol:
    rol = Rol.objects.filter(pk=identificador).first()
    if rol is None:
        raise DatosInvalidos({"rol": f"El rol «{identificador}» no existe."})
    return rol


def departamento_o_error(nombre: str) -> Departamento:
    """Los departamentos viajan por nombre, no por id, como dice el contrato.

    No se crean al vuelo: darlos de alta es trabajo del asistente de onboarding,
    y crearlos aquí por un dedazo llenaría el catálogo de duplicados.
    """
    departamento = Departamento.objects.filter(nombre__iexact=nombre).first()
    if departamento is None:
        raise DatosInvalidos({"departamento": f"El departamento «{nombre}» no existe."})
    return departamento


def usuario_o_404(identificador) -> Usuario:
    usuario = Usuario.objects.filter(pk=identificador).first()
    if usuario is None:
        raise NotFound("No existe un usuario con ese id.")
    return usuario


def dejaria_sin_administradores(usuario, nuevo_rol: str, nuevo_estado: str) -> bool:
    """¿Este cambio deja a la empresa sin ningún administrador activo?

    Solo puede pasar si quien se modifica era el último: si deja de ser
    administrador, o si se le suspende.
    """
    era = usuario.rol_id == Rol.ADMINISTRADOR and usuario.estado == EstadoUsuario.ACTIVO
    if not era:
        return False
    if nuevo_rol == Rol.ADMINISTRADOR and nuevo_estado == EstadoUsuario.ACTIVO:
        return False
    quedan_otros = (
        Usuario.objects.filter(rol_id=Rol.ADMINISTRADOR, estado=EstadoUsuario.ACTIVO)
        .exclude(pk=usuario.pk)
        .exists()
    )
    return not quedan_otros


# --- Vistas ------------------------------------------------------------------


class UserListCreateView(APIView):
    """`GET` y `POST /usuarios`."""

    permission_classes = [IsAuthenticated, requiere(Permiso.USUARIOS_ADMINISTRAR)]

    @extend_schema(
        tags=["usuarios"],
        operation_id="listUsers",
        summary="Lista los usuarios de la empresa",
        parameters=[
            OpenApiParameter("rol", str, description="Filtra por rol."),
            OpenApiParameter("estado", str, description="Filtra por estado."),
            OpenApiParameter("buscar", str, description="Coincidencia parcial en nombre o correo."),
        ],
        responses={200: UsuarioListSerializer},
    )
    def get(self, request):
        usuarios = Usuario.objects.select_related("departamento", "rol")

        rol = request.query_params.get("rol")
        if rol:
            usuarios = usuarios.filter(rol_id=rol)

        estado = request.query_params.get("estado")
        if estado:
            usuarios = usuarios.filter(estado=estado)

        buscar = (request.query_params.get("buscar") or "").strip()
        if buscar:
            usuarios = usuarios.filter(Q(nombre__icontains=buscar) | Q(correo__icontains=buscar))

        return Response({"resultados": [usuario_a_dict(u) for u in usuarios]})

    @extend_schema(
        tags=["usuarios"],
        operation_id="inviteUser",
        summary="Invita a un usuario",
        description=(
            "Crea la cuenta en estado `invitado`, sin contraseña. El correo con el "
            "enlace de activación todavía no se envía: depende de `/activate`."
        ),
        request=InvitacionSerializer,
        responses={201: UsuarioSerializer},
    )
    def post(self, request):
        cuerpo = InvitacionSerializer(data=request.data)
        if not cuerpo.is_valid():
            raise DatosInvalidos(cuerpo.errors)
        datos = cuerpo.validated_data

        correo = Usuario.objects.normalize_email(datos["correo"])
        if Usuario.objects.filter(correo__iexact=correo).exists():
            raise CorreoDuplicado()

        rol = rol_o_error(datos["rol"])
        nombre_departamento = (datos.get("departamento") or "").strip()
        departamento = departamento_o_error(nombre_departamento) if nombre_departamento else None

        # Sin contraseña: el manager lo deja en estado `invitado`.
        usuario = Usuario.objects.create_user(
            correo=correo, nombre=datos["nombre"], rol=rol, departamento=departamento
        )
        return Response(usuario_a_dict(usuario), status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """`GET` y `PATCH /usuarios/{id}`."""

    permission_classes = [IsAuthenticated, requiere(Permiso.USUARIOS_ADMINISTRAR)]

    @extend_schema(
        tags=["usuarios"],
        operation_id="getUser",
        summary="Consulta un usuario",
        responses={200: UsuarioSerializer},
    )
    def get(self, request, id):
        return Response(usuario_a_dict(usuario_o_404(id)))

    @extend_schema(
        tags=["usuarios"],
        operation_id="updateUser",
        summary="Cambia el rol, el departamento o suspende a un usuario",
        description=(
            "Requiere `usuarios:administrar`. Devuelve 403 si el cambio dejaría a la "
            "empresa sin ningún administrador activo."
        ),
        request=ActualizacionSerializer,
        responses={200: UsuarioSerializer},
    )
    def patch(self, request, id):
        usuario = usuario_o_404(id)
        cuerpo = ActualizacionSerializer(data=request.data)
        cuerpo.is_valid(raise_exception=True)
        datos = cuerpo.validated_data

        nuevo_rol = datos.get("rol", usuario.rol_id)
        nuevo_estado = datos.get("estado", usuario.estado)
        if dejaria_sin_administradores(usuario, nuevo_rol, nuevo_estado):
            raise SinAdministradores()

        campos: list[str] = []

        if "rol" in datos:
            usuario.rol = rol_o_error(datos["rol"])
            campos.append("rol")

        if "departamento" in datos:
            nombre = (datos["departamento"] or "").strip()
            usuario.departamento = departamento_o_error(nombre) if nombre else None
            campos.append("departamento")

        if "estado" in datos:
            usuario.estado = datos["estado"]
            campos.append("estado")
            # Reactivar a alguien suspendido no debe arrastrar intentos viejos.
            if datos["estado"] == EstadoUsuario.ACTIVO and usuario.intentos_fallidos:
                usuario.intentos_fallidos = 0
                campos.append("intentos_fallidos")

        usuario.save(update_fields=campos)
        usuario.refresh_from_db()
        return Response(usuario_a_dict(usuario))


class UserUnlockView(APIView):
    """`POST /usuarios/{id}/desbloquear`."""

    permission_classes = [IsAuthenticated, requiere(Permiso.USUARIOS_ADMINISTRAR)]

    @extend_schema(
        tags=["usuarios"],
        operation_id="unlockUser",
        summary="Reactiva una cuenta bloqueada por intentos fallidos",
        description="Reinicia el contador de intentos y devuelve la cuenta a `activo`.",
        request=None,
        responses={200: UsuarioSerializer},
    )
    def post(self, request, id):
        usuario = usuario_o_404(id)
        usuario.desbloquear()
        return Response(usuario_a_dict(usuario))
