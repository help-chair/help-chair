"""Pruebas de `/logout`.

Lo que se revoca es el **refresco**, no el acceso: el de acceso dura 15 minutos
y se valida por firma, sin consultar la base. Cerrar sesión corta la capacidad
de pedir uno nuevo.
"""

import pytest
from django.contrib.auth import get_user_model

from core.models import Permiso, Rol

LOGIN = "/api/access/v1/login"
LOGOUT = "/api/access/v1/logout"
REFRESH = "/api/access/v1/refresh"
CORREO = "ana@empresa-demo.mx"
PASSWORD = "clave-de-prueba-123"

Usuario = get_user_model()


@pytest.fixture
def usuario(db):
    rol = Rol.objects.create(id=Rol.AGENTE_N1, nombre="Agente N1", permisos=[Permiso.TICKETS_VER])
    return Usuario.objects.create_user(correo=CORREO, password=PASSWORD, nombre="Ana Ruiz", rol=rol)


def iniciar_sesion(client):
    respuesta = client.post(
        LOGIN, {"correo": CORREO, "password": PASSWORD}, content_type="application/json"
    )
    assert respuesta.status_code == 200, respuesta.content
    cuerpo = respuesta.json()
    return cuerpo["acceso"], cuerpo["refresco"]


def cerrar_sesion(client, acceso, refresco):
    return client.post(
        LOGOUT,
        {"refresco": refresco},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {acceso}",
    )


@pytest.mark.django_db
def test_cerrar_sesion_responde_204(client, usuario):
    acceso, refresco = iniciar_sesion(client)

    assert cerrar_sesion(client, acceso, refresco).status_code == 204


@pytest.mark.django_db
def test_el_refresco_revocado_ya_no_sirve(client, usuario):
    acceso, refresco = iniciar_sesion(client)
    cerrar_sesion(client, acceso, refresco)

    respuesta = client.post(REFRESH, {"refresco": refresco}, content_type="application/json")

    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_sin_sesion_no_se_puede_cerrar_sesion(client, usuario):
    _, refresco = iniciar_sesion(client)

    respuesta = client.post(LOGOUT, {"refresco": refresco}, content_type="application/json")

    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_un_refresco_invalido_tambien_responde_204(client, usuario):
    """El contrato lo pide así: responder distinto delataría qué tokens siguen vivos."""
    acceso, _ = iniciar_sesion(client)

    assert cerrar_sesion(client, acceso, "esto-no-es-un-token").status_code == 204


@pytest.mark.django_db
def test_cerrar_dos_veces_no_truena(client, usuario):
    acceso, refresco = iniciar_sesion(client)
    cerrar_sesion(client, acceso, refresco)

    assert cerrar_sesion(client, acceso, refresco).status_code == 204


@pytest.mark.django_db
def test_sin_el_campo_refresco_responde_400(client, usuario):
    acceso, _ = iniciar_sesion(client)

    respuesta = client.post(
        LOGOUT, {}, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {acceso}"
    )

    assert respuesta.status_code == 400
