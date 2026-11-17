"""Pruebas del login con JWT."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from core.models import EstadoUsuario, Permiso, Rol

LOGIN = "/api/access/v1/login"
REFRESH = "/api/access/v1/refresh"
CORREO = "ana@empresa-demo.mx"
CLAVE = "clave-de-prueba-123"

Usuario = get_user_model()


@pytest.fixture
def rol_agente(db):
    return Rol.objects.create(
        id=Rol.AGENTE_N1,
        nombre="Agente N1",
        permisos=[Permiso.TICKETS_VER, Permiso.TICKETS_ATENDER],
    )


@pytest.fixture
def usuario(db, rol_agente):
    return Usuario.objects.create_user(
        correo=CORREO, password=CLAVE, nombre="Ana Ruiz", rol=rol_agente
    )


def _login(client, correo=CORREO, clave=CLAVE):
    return client.post(
        LOGIN, {"correo": correo, "password": clave}, content_type="application/json"
    )


@pytest.mark.django_db
def test_login_entrega_los_dos_tokens(client, usuario):
    respuesta = _login(client)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["access"]
    assert cuerpo["refresh"]


@pytest.mark.django_db
def test_el_token_lleva_los_claims_del_contrato(client, usuario, settings):
    token = AccessToken(_login(client).json()["access"])

    assert token["empresa"] == settings.EMPRESA_ID
    assert token["rol"] == Rol.AGENTE_N1
    assert token["permisos"] == [Permiso.TICKETS_VER, Permiso.TICKETS_ATENDER]
    assert token["sub"] == str(usuario.id)
    assert token["exp"] > token["iat"]


@pytest.mark.django_db
def test_un_usuario_sin_rol_entra_como_usuario_final(client):
    Usuario.objects.create_user(correo="sin.rol@empresa-demo.mx", password=CLAVE)

    token = AccessToken(_login(client, correo="sin.rol@empresa-demo.mx").json()["access"])

    assert token["rol"] == Rol.USUARIO_FINAL
    assert token["permisos"] == []


@pytest.mark.django_db
def test_contrasena_incorrecta_devuelve_401(client, usuario):
    assert _login(client, clave="no-es-la-clave").status_code == 401


@pytest.mark.django_db
def test_usuario_inexistente_devuelve_401(client, db):
    assert _login(client, correo="nadie@empresa-demo.mx").status_code == 401


@pytest.mark.django_db
def test_un_invitado_no_puede_entrar(client, usuario):
    usuario.estado = EstadoUsuario.INVITADO
    usuario.save(update_fields=["estado"])

    assert _login(client).status_code == 401


@pytest.mark.django_db
def test_un_bloqueado_no_puede_entrar(client, usuario):
    usuario.estado = EstadoUsuario.BLOQUEADO
    usuario.save(update_fields=["estado"])

    assert _login(client).status_code == 401


@pytest.mark.django_db
def test_entrar_bien_limpia_los_intentos_fallidos(client, usuario):
    usuario.intentos_fallidos = 3
    usuario.save(update_fields=["intentos_fallidos"])

    _login(client)

    usuario.refresh_from_db()
    assert usuario.intentos_fallidos == 0


@pytest.mark.django_db
def test_refresh_entrega_un_acceso_nuevo(client, usuario):
    refresh = _login(client).json()["refresh"]

    respuesta = client.post(REFRESH, {"refresh": refresh}, content_type="application/json")

    assert respuesta.status_code == 200
    assert respuesta.json()["access"]


@pytest.mark.django_db
def test_refresh_invalido_devuelve_401(client):
    respuesta = client.post(
        REFRESH, {"refresh": "token-inventado"}, content_type="application/json"
    )

    assert respuesta.status_code == 401
