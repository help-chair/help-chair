"""Pruebas de `/me` y `/me/onboarding` (tag `cuenta` del contrato).

`/me` existe para que el frontend sepa quién entró sin repetir el login, y
`/me/onboarding` para que el asistente cierre la configuración inicial. Las dos
responden el esquema `UsuarioActual`, así que se comprueba el mismo contrato.
"""

import pytest
from django.contrib.auth import get_user_model

from core.models import Departamento, Perfil, Permiso, Rol

LOGIN = "/api/access/v1/login"
ME = "/api/access/v1/me"
ONBOARDING = "/api/access/v1/me/onboarding"
PASSWORD = "clave-de-prueba-123"

Usuario = get_user_model()


# --- Ayudantes ---------------------------------------------------------------


@pytest.fixture
def admin_role(db):
    return Rol.objects.create(
        id=Rol.ADMINISTRADOR,
        nombre="Administrador",
        permisos=[Permiso.EMPRESA_CONFIGURAR, Permiso.USUARIOS_ADMINISTRAR],
    )


@pytest.fixture
def end_user_role(db):
    return Rol.objects.create(
        id=Rol.USUARIO_FINAL,
        nombre="Usuario final",
        permisos=[Permiso.TICKETS_VER],
    )


@pytest.fixture
def admin(db, admin_role):
    return Usuario.objects.create_user(
        correo="admin@empresa-demo.mx", password=PASSWORD, nombre="Val Ortiz", rol=admin_role
    )


@pytest.fixture
def end_user(db, end_user_role):
    return Usuario.objects.create_user(
        correo="pedro@empresa-demo.mx", password=PASSWORD, nombre="Pedro Lara", rol=end_user_role
    )


def token_for(client, correo):
    respuesta = client.post(
        LOGIN, {"correo": correo, "password": PASSWORD}, content_type="application/json"
    )
    assert respuesta.status_code == 200, respuesta.content
    return respuesta.json()["acceso"]


def auth(client, correo):
    return {"HTTP_AUTHORIZATION": f"Bearer {token_for(client, correo)}"}


# --- GET /me -----------------------------------------------------------------


@pytest.mark.django_db
def test_me_sin_token_responde_401(client):
    assert client.get(ME).status_code == 401


@pytest.mark.django_db
def test_me_devuelve_el_usuario_actual_del_contrato(client, admin):
    respuesta = client.get(ME, **auth(client, admin.correo))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == str(admin.id)
    assert cuerpo["correo"] == admin.correo
    assert cuerpo["nombre"] == "Val Ortiz"
    assert cuerpo["rol"] == Rol.ADMINISTRADOR
    assert cuerpo["estado"] == admin.estado
    assert set(cuerpo["permisos"]) == {
        Permiso.EMPRESA_CONFIGURAR.value,
        Permiso.USUARIOS_ADMINISTRAR.value,
    }
    assert cuerpo["onboarding_completed"] is False


@pytest.mark.django_db
def test_me_nombra_el_departamento_cuando_lo_hay(client, admin):
    admin.departamento = Departamento.objects.create(nombre="Sistemas")
    admin.save(update_fields=["departamento"])

    cuerpo = client.get(ME, **auth(client, admin.correo)).json()

    assert cuerpo["departamento"] == "Sistemas"


@pytest.mark.django_db
def test_me_deja_el_departamento_en_nulo_si_no_tiene(client, end_user):
    cuerpo = client.get(ME, **auth(client, end_user.correo)).json()

    assert cuerpo["departamento"] is None


# --- PATCH /me/onboarding ----------------------------------------------------


@pytest.mark.django_db
def test_onboarding_sin_token_responde_401(client):
    respuesta = client.patch(ONBOARDING, {"completed": True}, content_type="application/json")

    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_un_usuario_final_no_puede_cerrar_el_onboarding(client, end_user):
    respuesta = client.patch(
        ONBOARDING,
        {"completed": True},
        content_type="application/json",
        **auth(client, end_user.correo),
    )

    assert respuesta.status_code == 403
    assert Perfil.objects.filter(usuario=end_user).count() == 0


@pytest.mark.django_db
def test_el_administrador_cierra_el_onboarding(client, admin):
    respuesta = client.patch(
        ONBOARDING,
        {"completed": True},
        content_type="application/json",
        **auth(client, admin.correo),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["onboarding_completed"] is True
    assert Perfil.objects.get(usuario=admin).onboarding_completado is True


@pytest.mark.django_db
def test_cerrar_el_onboarding_dos_veces_no_cambia_nada(client, admin):
    cabeceras = auth(client, admin.correo)
    cuerpo = {"completed": True}

    primera = client.patch(ONBOARDING, cuerpo, content_type="application/json", **cabeceras)
    segunda = client.patch(ONBOARDING, cuerpo, content_type="application/json", **cabeceras)

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert segunda.json()["onboarding_completed"] is True
    assert Perfil.objects.filter(usuario=admin).count() == 1


@pytest.mark.django_db
def test_el_onboarding_no_se_puede_reabrir(client, admin):
    respuesta = client.patch(
        ONBOARDING,
        {"completed": False},
        content_type="application/json",
        **auth(client, admin.correo),
    )

    assert respuesta.status_code == 400
    assert Perfil.objects.filter(usuario=admin, onboarding_completado=True).count() == 0


@pytest.mark.django_db
def test_despues_de_cerrarlo_me_ya_lo_reporta(client, admin):
    cabeceras = auth(client, admin.correo)
    client.patch(ONBOARDING, {"completed": True}, content_type="application/json", **cabeceras)

    cuerpo = client.get(ME, **cabeceras).json()

    assert cuerpo["onboarding_completed"] is True
