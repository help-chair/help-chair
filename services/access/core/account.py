"""Cuenta de quien tiene la sesión abierta: su perfil y el estado del onboarding.

Implementa `/api/access/v1/me` y `/api/access/v1/me/onboarding`, el tag `cuenta`
de `contracts/access/openapi.yaml`.

Las dos responden el mismo esquema `UsuarioActual` que ya devuelve el login, así
que reutilizan `usuario_actual` y `UsuarioActualSerializer` de `auth.py` en vez de
repetir la forma del contrato en dos lugares: si el contrato cambia, se toca uno.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import UsuarioActualSerializer, usuario_actual
from .models import Perfil, Permiso
from .permissions import requiere


class OnboardingUpdateSerializer(serializers.Serializer):
    """Cuerpo de `PATCH /me/onboarding`.

    El contrato fija `completed` en `true` (`enum: [true]`): el asistente solo
    marca el final del onboarding, nunca lo reabre. Mandar `false` es un 400,
    no un no-op silencioso, para que el frontend se entere de que pidió algo
    que este endpoint no hace.
    """

    completed = serializers.BooleanField()

    def validate_completed(self, value: bool) -> bool:
        if value is not True:
            raise serializers.ValidationError("El onboarding solo puede marcarse como terminado.")
        return value


@extend_schema(
    tags=["cuenta"],
    operation_id="getCurrentUser",
    summary="Perfil del usuario de la sesión",
    description=(
        "El frontend lo consulta al cargar el Service Desk: de `onboarding_completed` "
        "depende que se muestre el asistente, y de `permisos` qué secciones se dibujan."
    ),
    responses={200: UsuarioActualSerializer},
)
class CurrentUserView(APIView):
    """`GET /me`: el usuario del token, sin tener que volver a hacer login."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(usuario_actual(request.user))


@extend_schema(
    tags=["cuenta"],
    operation_id="updateOnboardingState",
    summary="Marca el onboarding como terminado",
    description=(
        "Lo llama el asistente de onboarding al guardar el último paso. Pide el "
        "permiso `empresa:configurar`, que solo trae el rol administrador.\n\n"
        "Es idempotente: repetirlo deja el mismo estado y responde 200."
    ),
    request=OnboardingUpdateSerializer,
    responses={200: UsuarioActualSerializer},
)
class OnboardingView(APIView):
    """`PATCH /me/onboarding`: cierra el asistente para toda la empresa.

    Se pregunta por el permiso y no por el rol, como el resto del servicio: así
    un rol nuevo con `empresa:configurar` no obliga a volver aquí.
    """

    permission_classes = [IsAuthenticated, requiere(Permiso.EMPRESA_CONFIGURAR)]

    def patch(self, request):
        cuerpo = OnboardingUpdateSerializer(data=request.data)
        cuerpo.is_valid(raise_exception=True)

        perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
        if not perfil.onboarding_completado:
            perfil.onboarding_completado = True
            perfil.save(update_fields=["onboarding_completado", "actualizado_en"])

        # `usuario_actual` lee el perfil desde la relación cacheada del usuario;
        # si el perfil se acaba de crear, esa caché todavía está vacía.
        request.user.perfil = perfil
        return Response(usuario_actual(request.user))
