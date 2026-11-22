"""Pruebas de los permisos por rol.

Dos niveles: la lógica de la clase de permiso por su cuenta, y una vista real
protegida, para comprobar que el 403 sale con el código del contrato.
"""

import json

import pytest
from django.urls import path
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.auth import LoginView
from core.models import Permiso, Rol, Usuario
from core.permissions import permisos_de, requiere

CLAVE = "clave-de-prueba-123"


# --- Vista de prueba, protegida con un permiso de administrador --------------


class VistaProtegida(APIView):
    permission_classes = [requiere(Permiso.USUARIOS_ADMINISTRAR)]

    def get(self, request):
        return Response({"ok": True})


urlpatterns = [
    path("api/access/v1/login", LoginView.as_view()),
    path("prueba/solo-admin", VistaProtegida.as_view()),
]


# --- Ayudantes ---------------------------------------------------------------


def crear_rol(identificador, permisos):
    return Rol.objects.create(id=identificador, nombre=identificador, permisos=permisos)


def crear_usuario(correo, rol):
    return Usuario.objects.create_user(correo=correo, password=CLAVE, nombre="Prueba", rol=rol)


def token_de(client, correo):
    respuesta = client.post(
        "/api/access/v1/login",
        json.dumps({"correo": correo, "password": CLAVE}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200, respuesta.content
    return respuesta.json()["acceso"]


# --- La lógica de la clase, sin pasar por HTTP -------------------------------


class PeticionFalsa:
    """Lo mínimo que mira la clase de permiso: el usuario y el token."""

    def __init__(self, permisos=None, autenticado=True):
        self.auth = None if permisos is None else {"permisos": permisos}
        self.user = type("U", (), {"is_authenticated": autenticado, "permisos": []})()


def test_el_permiso_se_concede_si_el_token_lo_trae():
    permiso = requiere(Permiso.USUARIOS_ADMINISTRAR)()

    assert permiso.has_permission(PeticionFalsa([Permiso.USUARIOS_ADMINISTRAR]), None) is True


def test_el_permiso_se_niega_si_el_token_no_lo_trae():
    permiso = requiere(Permiso.USUARIOS_ADMINISTRAR)()

    assert permiso.has_permission(PeticionFalsa([Permiso.TICKETS_VER]), None) is False


def test_basta_uno_de_los_permisos_pedidos():
    permiso = requiere(Permiso.TICKETS_ATENDER, Permiso.TICKETS_ESCALAR)()

    assert permiso.has_permission(PeticionFalsa([Permiso.TICKETS_ESCALAR]), None) is True


def test_sin_sesion_no_hay_permiso():
    permiso = requiere(Permiso.TICKETS_VER)()

    assert permiso.has_permission(PeticionFalsa(None, autenticado=False), None) is False


def test_los_permisos_se_leen_del_token_y_no_de_la_base():
    """El token es la fuente: así los demás servicios no consultan a Accesos."""
    peticion = PeticionFalsa([Permiso.EMPRESA_CONFIGURAR])

    assert permisos_de(peticion) == {Permiso.EMPRESA_CONFIGURAR}


@pytest.mark.django_db
def test_sin_token_se_cae_al_rol_de_la_base():
    """Para la sesión del admin de Django, que no trae token."""
    rol = crear_rol(Rol.ADMINISTRADOR, [Permiso.USUARIOS_ADMINISTRAR])
    peticion = APIRequestFactory().get("/prueba/solo-admin")
    peticion.user = crear_usuario("ana@empresa-demo.mx", rol)
    peticion.auth = None

    assert permisos_de(peticion) == {Permiso.USUARIOS_ADMINISTRAR}


# --- La vista real, con el token de verdad ----------------------------------


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_un_administrador_entra_a_la_vista_protegida(client):
    rol = crear_rol(Rol.ADMINISTRADOR, [Permiso.USUARIOS_ADMINISTRAR])
    crear_usuario("admin@empresa-demo.mx", rol)
    token = token_de(client, "admin@empresa-demo.mx")

    respuesta = client.get("/prueba/solo-admin", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True}


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_un_usuario_final_recibe_403_con_el_codigo_del_contrato(client):
    rol = crear_rol(Rol.USUARIO_FINAL, [Permiso.TICKETS_VER])
    crear_usuario("lucia@empresa-demo.mx", rol)
    token = token_de(client, "lucia@empresa-demo.mx")

    respuesta = client.get("/prueba/solo-admin", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert respuesta.status_code == 403
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "permiso_denegado"
    assert cuerpo["detalle"]


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_sin_token_la_vista_protegida_responde_401(client):
    respuesta = client.get("/prueba/solo-admin")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
