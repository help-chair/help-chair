"""Pruebas de `/roles` y `/departamentos`.

El frontend dibuja con esto los selectores de los formularios de usuario, así
que lo que se comprueba es la forma del contrato: `{resultados: [...]}`.
"""

import pytest
from django.contrib.auth import get_user_model

from core.models import Departamento, Permiso, Rol

LOGIN = "/api/access/v1/login"
ROLES = "/api/access/v1/roles"
DEPARTAMENTOS = "/api/access/v1/departamentos"
PASSWORD = "clave-de-prueba-123"

Usuario = get_user_model()


# --- Ayudantes ---------------------------------------------------------------


@pytest.fixture
def admin_role(db):
    return Rol.objects.create(
        id=Rol.ADMINISTRADOR,
        nombre="Administrador",
        descripcion="Configura la empresa y administra usuarios.",
        permisos=[Permiso.EMPRESA_CONFIGURAR, Permiso.USUARIOS_ADMINISTRAR],
    )


@pytest.fixture
def end_user_role(db):
    return Rol.objects.create(
        id=Rol.USUARIO_FINAL, nombre="Usuario final", permisos=[Permiso.TICKETS_VER]
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


def auth(client, correo):
    respuesta = client.post(
        LOGIN, {"correo": correo, "password": PASSWORD}, content_type="application/json"
    )
    assert respuesta.status_code == 200, respuesta.content
    return {"HTTP_AUTHORIZATION": f"Bearer {respuesta.json()['acceso']}"}


def crear(client, cabeceras, nombre):
    return client.post(
        DEPARTAMENTOS, {"nombre": nombre}, content_type="application/json", **cabeceras
    )


# --- GET /roles --------------------------------------------------------------


@pytest.mark.django_db
def test_roles_sin_token_responde_401(client):
    assert client.get(ROLES).status_code == 401


@pytest.mark.django_db
def test_roles_lista_el_catalogo_con_sus_permisos(client, admin, end_user_role):
    cuerpo = client.get(ROLES, **auth(client, admin.correo)).json()

    por_id = {rol["id"]: rol for rol in cuerpo["resultados"]}
    assert set(por_id) == {Rol.ADMINISTRADOR, Rol.USUARIO_FINAL}
    administrador = por_id[Rol.ADMINISTRADOR]
    assert administrador["nombre"] == "Administrador"
    assert administrador["descripcion"] == "Configura la empresa y administra usuarios."
    assert set(administrador["permisos"]) == {
        Permiso.EMPRESA_CONFIGURAR.value,
        Permiso.USUARIOS_ADMINISTRAR.value,
    }


@pytest.mark.django_db
def test_un_usuario_final_tambien_puede_leer_los_roles(client, end_user):
    respuesta = client.get(ROLES, **auth(client, end_user.correo))

    assert respuesta.status_code == 200


# --- GET /departamentos ------------------------------------------------------


@pytest.mark.django_db
def test_departamentos_sin_token_responde_401(client):
    assert client.get(DEPARTAMENTOS).status_code == 401


@pytest.mark.django_db
def test_departamentos_lista_vacia_cuando_no_hay(client, admin):
    cuerpo = client.get(DEPARTAMENTOS, **auth(client, admin.correo)).json()

    assert cuerpo == {"resultados": []}


@pytest.mark.django_db
def test_departamentos_cuenta_cuantos_usuarios_tiene_cada_uno(client, admin):
    sistemas = Departamento.objects.create(nombre="Sistemas")
    Departamento.objects.create(nombre="Ventas")
    admin.departamento = sistemas
    admin.save(update_fields=["departamento"])

    cuerpo = client.get(DEPARTAMENTOS, **auth(client, admin.correo)).json()

    por_nombre = {d["nombre"]: d for d in cuerpo["resultados"]}
    assert por_nombre["Sistemas"]["usuarios"] == 1
    assert por_nombre["Ventas"]["usuarios"] == 0


# --- POST /departamentos -----------------------------------------------------


@pytest.mark.django_db
def test_un_usuario_final_no_puede_crear_departamentos(client, end_user):
    respuesta = crear(client, auth(client, end_user.correo), "Sistemas")

    assert respuesta.status_code == 403
    assert Departamento.objects.count() == 0


@pytest.mark.django_db
def test_el_administrador_crea_un_departamento(client, admin):
    respuesta = crear(client, auth(client, admin.correo), "Sistemas")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Sistemas"
    assert cuerpo["usuarios"] == 0
    assert cuerpo["id"]
    assert Departamento.objects.filter(nombre="Sistemas").exists()


@pytest.mark.django_db
def test_no_se_puede_repetir_el_nombre(client, admin):
    cabeceras = auth(client, admin.correo)
    crear(client, cabeceras, "Sistemas")

    respuesta = crear(client, cabeceras, "Sistemas")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "departamento_duplicado"
    assert Departamento.objects.count() == 1


@pytest.mark.django_db
def test_el_nombre_repetido_se_detecta_sin_importar_mayusculas(client, admin):
    cabeceras = auth(client, admin.correo)
    crear(client, cabeceras, "Sistemas")

    respuesta = crear(client, cabeceras, "sistemas")

    assert respuesta.status_code == 409
    assert Departamento.objects.count() == 1


@pytest.mark.django_db
def test_el_nombre_no_puede_ir_vacio(client, admin):
    respuesta = crear(client, auth(client, admin.correo), "   ")

    assert respuesta.status_code == 400
    assert Departamento.objects.count() == 0


@pytest.mark.django_db
def test_el_nombre_no_pasa_de_80_caracteres(client, admin):
    respuesta = crear(client, auth(client, admin.correo), "S" * 81)

    assert respuesta.status_code == 400
    assert "nombre" in respuesta.json().get("campos", {})
    assert Departamento.objects.count() == 0
