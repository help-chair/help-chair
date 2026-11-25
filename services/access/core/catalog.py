"""Catálogos que el frontend necesita para dibujar sus formularios: roles y departamentos.

Implementa `/api/access/v1/roles` y `/api/access/v1/departamentos` del contrato
`contracts/access/openapi.yaml`.

Los roles son de solo lectura: en la v1 son fijos y se cargan con `make seed`.
Los departamentos sí se crean, porque el asistente de onboarding los da de alta.
"""

from django.db import IntegrityError
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Departamento, Permiso, Rol
from .permissions import requiere

# El contrato limita el nombre a 80 caracteres; el modelo acepta 100. Se valida
# con el del contrato, que es el que ve quien consume la API.
NOMBRE_MAX = 80


class DepartamentoDuplicado(APIException):
    """409 del contrato: ya existe un departamento con ese nombre."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "departamento_duplicado"
    default_detail = "Ya existe un departamento con ese nombre."


class RolSerializer(serializers.Serializer):
    """Esquema `Rol` del contrato."""

    id = serializers.CharField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()
    permisos = serializers.ListField(child=serializers.CharField())


class DepartamentoSerializer(serializers.Serializer):
    """Esquema `Departamento` del contrato: incluye cuántos usuarios tiene."""

    id = serializers.UUIDField()
    nombre = serializers.CharField()
    usuarios = serializers.IntegerField()


class RolListSerializer(serializers.Serializer):
    resultados = RolSerializer(many=True)


class DepartamentoListSerializer(serializers.Serializer):
    resultados = DepartamentoSerializer(many=True)


class DepartamentoCreateSerializer(serializers.Serializer):
    """Cuerpo de `POST /departamentos`."""

    nombre = serializers.CharField(max_length=NOMBRE_MAX, trim_whitespace=True)

    def validate_nombre(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede ir vacío.")
        return value.strip()


def departamento_a_dict(departamento, total_usuarios: int) -> dict:
    return {
        "id": str(departamento.id),
        "nombre": departamento.nombre,
        "usuarios": total_usuarios,
    }


@extend_schema(
    tags=["usuarios"],
    operation_id="listRoles",
    summary="Catálogo de roles y sus permisos",
    description="Los roles son fijos en la v1; el frontend los lee para dibujar los selectores.",
    responses={200: RolListSerializer},
)
class RoleListView(APIView):
    """`GET /roles`: catálogo completo, sin paginar (son cuatro)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = [
            {
                "id": rol.id,
                "nombre": rol.nombre,
                "descripcion": rol.descripcion,
                "permisos": list(rol.permisos or []),
            }
            for rol in Rol.objects.all()
        ]
        return Response({"resultados": roles})


class DepartmentsView(APIView):
    """`GET` y `POST /departamentos`.

    Leer el catálogo lo puede hacer cualquiera con sesión, porque el selector de
    departamento aparece en formularios que no son de administración. Crear pide
    `empresa:configurar`, que es lo que trae el administrador.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), requiere(Permiso.EMPRESA_CONFIGURAR)()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["usuarios"],
        operation_id="listDepartments",
        summary="Lista los departamentos de la empresa",
        responses={200: DepartamentoListSerializer},
    )
    def get(self, request):
        departamentos = Departamento.objects.annotate(total_usuarios=Count("usuarios"))
        return Response(
            {
                "resultados": [
                    departamento_a_dict(departamento, departamento.total_usuarios)
                    for departamento in departamentos
                ]
            }
        )

    @extend_schema(
        tags=["usuarios"],
        operation_id="createDepartment",
        summary="Crea un departamento",
        description="Lo usa el asistente de onboarding. Requiere `empresa:configurar`.",
        request=DepartamentoCreateSerializer,
        responses={201: DepartamentoSerializer},
    )
    def post(self, request):
        cuerpo = DepartamentoCreateSerializer(data=request.data)
        cuerpo.is_valid(raise_exception=True)
        nombre = cuerpo.validated_data["nombre"]

        # Se compara sin distinguir mayúsculas: «Sistemas» y «sistemas» son el
        # mismo departamento para quien lo lee, aunque la base los dejaría pasar.
        if Departamento.objects.filter(nombre__iexact=nombre).exists():
            raise DepartamentoDuplicado()

        try:
            departamento = Departamento.objects.create(nombre=nombre)
        except IntegrityError as error:
            # Dos altas simultáneas con el mismo nombre: la base es la que manda.
            raise DepartamentoDuplicado() from error

        return Response(departamento_a_dict(departamento, 0), status=status.HTTP_201_CREATED)
