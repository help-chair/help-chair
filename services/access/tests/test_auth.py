"""Pruebas del login con JWT.

No dependen de cómo quede el modelo de usuario: leen ``USERNAME_FIELD``, así
que siguen sirviendo cuando el equipo defina su propio ``AUTH_USER_MODEL``.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

LOGIN = "/api/auth/login"
REFRESH = "/api/auth/refresh"
CLAVE = "clave-de-prueba-123"


@pytest.fixture
def credenciales():
    Usuario = get_user_model()
    campo = Usuario.USERNAME_FIELD
    valor = "ana@empresa-demo.mx" if campo == "email" else "ana"
    return campo, valor


@pytest.fixture
def usuario(db, credenciales):
    campo, valor = credenciales
    Usuario = get_user_model()
    return Usuario.objects.create_user(**{campo: valor}, password=CLAVE)


def _login(client, campo, valor, clave=CLAVE):
    return client.post(LOGIN, {campo: valor, "password": clave}, content_type="application/json")


@pytest.mark.django_db
def test_login_entrega_los_dos_tokens(client, usuario, credenciales):
    campo, valor = credenciales
    respuesta = _login(client, campo, valor)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["access"]
    assert cuerpo["refresh"]


@pytest.mark.django_db
def test_el_token_lleva_empresa_rol_y_expiracion(client, usuario, credenciales, settings):
    campo, valor = credenciales
    respuesta = _login(client, campo, valor)

    token = AccessToken(respuesta.json()["access"])
    assert token["empresa"] == settings.EMPRESA_ID
    assert token["rol"] == "usuario"
    assert token["exp"] > token["iat"]


@pytest.mark.django_db
def test_el_rol_de_un_superusuario_es_administrador(client, credenciales):
    campo, valor = credenciales
    Usuario = get_user_model()
    Usuario.objects.create_superuser(**{campo: valor}, password=CLAVE)

    respuesta = _login(client, campo, valor)

    assert AccessToken(respuesta.json()["access"])["rol"] == "administrador"


@pytest.mark.django_db
def test_contrasena_incorrecta_devuelve_401(client, usuario, credenciales):
    campo, valor = credenciales

    respuesta = _login(client, campo, valor, clave="no-es-la-clave")

    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_usuario_inexistente_devuelve_401(client, credenciales):
    campo, _ = credenciales

    respuesta = _login(client, campo, "nadie@empresa-demo.mx")

    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_refresh_entrega_un_acceso_nuevo(client, usuario, credenciales):
    campo, valor = credenciales
    refresh = _login(client, campo, valor).json()["refresh"]

    respuesta = client.post(REFRESH, {"refresh": refresh}, content_type="application/json")

    assert respuesta.status_code == 200
    assert respuesta.json()["access"]


@pytest.mark.django_db
def test_refresh_invalido_devuelve_401(client):
    respuesta = client.post(
        REFRESH, {"refresh": "token-inventado"}, content_type="application/json"
    )

    assert respuesta.status_code == 401
