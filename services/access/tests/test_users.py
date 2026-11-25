"""Pruebas de `/usuarios`, `/usuarios/{id}` y `/usuarios/{id}/desbloquear`.

Es la pantalla de administración del frontend, así que se comprueban las tres
cosas que la sostienen: que solo entre quien tiene `usuarios:administrar`, que
los filtros respondan, y que la empresa no pueda quedarse sin administrador.
"""

import uuid

import pytest
from django.contrib.auth import get_user_model

from core.models import Departamento, EstadoUsuario, Permiso, Rol

LOGIN = "/api/access/v1/login"
USUARIOS = "/api/access/v1/usuarios"
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
def agent_role(db):
    return Rol.objects.create(
        id=Rol.AGENTE_N1, nombre="Agente N1", permisos=[Permiso.TICKETS_ATENDER]
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
def agent(db, agent_role):
    return Usuario.objects.create_user(
        correo="ana@empresa-demo.mx", password=PASSWORD, nombre="Ana Ruiz", rol=agent_role
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


def invitar(client, cabeceras, **datos):
    cuerpo = {"nombre": "Nuevo Usuario", "correo": "nuevo@empresa-demo.mx", "rol": Rol.AGENTE_N1}
    cuerpo.update(datos)
    return client.post(USUARIOS, cuerpo, content_type="application/json", **cabeceras)


def modificar(client, cabeceras, usuario, **datos):
    return client.patch(
        f"{USUARIOS}/{usuario.id}", datos, content_type="application/json", **cabeceras
    )


# --- GET /usuarios -----------------------------------------------------------


@pytest.mark.django_db
def test_listar_sin_token_responde_401(client):
    assert client.get(USUARIOS).status_code == 401


@pytest.mark.django_db
def test_un_usuario_final_no_puede_listar_usuarios(client, end_user):
    assert client.get(USUARIOS, **auth(client, end_user.correo)).status_code == 403


@pytest.mark.django_db
def test_el_administrador_lista_a_todos(client, admin, agent, end_user):
    cuerpo = client.get(USUARIOS, **auth(client, admin.correo)).json()

    correos = {u["correo"] for u in cuerpo["resultados"]}
    assert correos == {admin.correo, agent.correo, end_user.correo}


@pytest.mark.django_db
def test_filtra_por_rol(client, admin, agent, end_user):
    cuerpo = client.get(USUARIOS, {"rol": Rol.AGENTE_N1}, **auth(client, admin.correo)).json()

    assert [u["correo"] for u in cuerpo["resultados"]] == [agent.correo]


@pytest.mark.django_db
def test_filtra_por_estado(client, admin, agent):
    agent.estado = EstadoUsuario.SUSPENDIDO
    agent.save(update_fields=["estado"])

    cuerpo = client.get(
        USUARIOS, {"estado": EstadoUsuario.SUSPENDIDO}, **auth(client, admin.correo)
    ).json()

    assert [u["correo"] for u in cuerpo["resultados"]] == [agent.correo]


@pytest.mark.django_db
def test_busca_por_pedazo_del_nombre(client, admin, agent):
    cuerpo = client.get(USUARIOS, {"buscar": "ruiz"}, **auth(client, admin.correo)).json()

    assert [u["correo"] for u in cuerpo["resultados"]] == [agent.correo]


@pytest.mark.django_db
def test_busca_por_pedazo_del_correo(client, admin, agent):
    cuerpo = client.get(USUARIOS, {"buscar": "ana@"}, **auth(client, admin.correo)).json()

    assert [u["correo"] for u in cuerpo["resultados"]] == [agent.correo]


# --- POST /usuarios (invitación) ---------------------------------------------


@pytest.mark.django_db
def test_un_usuario_final_no_puede_invitar(client, end_user, agent_role):
    assert invitar(client, auth(client, end_user.correo)).status_code == 403


@pytest.mark.django_db
def test_la_invitacion_crea_la_cuenta_sin_contrasena(client, admin, agent_role):
    respuesta = invitar(client, auth(client, admin.correo))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["correo"] == "nuevo@empresa-demo.mx"
    assert cuerpo["estado"] == EstadoUsuario.INVITADO
    assert cuerpo["rol"] == Rol.AGENTE_N1

    invitado = Usuario.objects.get(correo="nuevo@empresa-demo.mx")
    assert not invitado.has_usable_password()
    assert not invitado.is_active


@pytest.mark.django_db
def test_la_invitacion_asigna_el_departamento_por_nombre(client, admin, agent_role):
    Departamento.objects.create(nombre="Sistemas")

    cuerpo = invitar(client, auth(client, admin.correo), departamento="Sistemas").json()

    assert cuerpo["departamento"] == "Sistemas"


@pytest.mark.django_db
def test_no_se_puede_invitar_un_correo_que_ya_existe(client, admin, agent, agent_role):
    respuesta = invitar(client, auth(client, admin.correo), correo=agent.correo)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "correo_duplicado"


@pytest.mark.django_db
def test_invitar_con_un_rol_inexistente_responde_422(client, admin):
    respuesta = invitar(client, auth(client, admin.correo), rol="inventado")

    assert respuesta.status_code == 422
    assert "rol" in respuesta.json().get("campos", {})


@pytest.mark.django_db
def test_invitar_a_un_departamento_inexistente_responde_422(client, admin, agent_role):
    respuesta = invitar(client, auth(client, admin.correo), departamento="Marte")

    assert respuesta.status_code == 422
    assert Usuario.objects.filter(correo="nuevo@empresa-demo.mx").count() == 0


@pytest.mark.django_db
def test_invitar_con_un_correo_mal_escrito_responde_422(client, admin, agent_role):
    respuesta = invitar(client, auth(client, admin.correo), correo="esto-no-es-correo")

    assert respuesta.status_code == 422
    assert "correo" in respuesta.json().get("campos", {})


# --- GET /usuarios/{id} ------------------------------------------------------


@pytest.mark.django_db
def test_consulta_un_usuario_por_id(client, admin, agent):
    respuesta = client.get(f"{USUARIOS}/{agent.id}", **auth(client, admin.correo))

    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == agent.correo


@pytest.mark.django_db
def test_un_id_que_no_existe_responde_404(client, admin):
    respuesta = client.get(f"{USUARIOS}/{uuid.uuid4()}", **auth(client, admin.correo))

    assert respuesta.status_code == 404


# --- PATCH /usuarios/{id} ----------------------------------------------------


@pytest.mark.django_db
def test_cambia_el_rol_de_un_usuario(client, admin, agent, end_user_role):
    respuesta = modificar(client, auth(client, admin.correo), agent, rol=Rol.USUARIO_FINAL)

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == Rol.USUARIO_FINAL
    agent.refresh_from_db()
    assert agent.rol_id == Rol.USUARIO_FINAL


@pytest.mark.django_db
def test_cambia_el_departamento(client, admin, agent):
    Departamento.objects.create(nombre="Soporte")

    cuerpo = modificar(client, auth(client, admin.correo), agent, departamento="Soporte").json()

    assert cuerpo["departamento"] == "Soporte"


@pytest.mark.django_db
def test_quita_el_departamento_con_null(client, admin, agent):
    agent.departamento = Departamento.objects.create(nombre="Soporte")
    agent.save(update_fields=["departamento"])

    cuerpo = modificar(client, auth(client, admin.correo), agent, departamento=None).json()

    assert cuerpo["departamento"] is None


@pytest.mark.django_db
def test_suspende_a_un_usuario(client, admin, agent):
    cuerpo = modificar(
        client, auth(client, admin.correo), agent, estado=EstadoUsuario.SUSPENDIDO
    ).json()

    assert cuerpo["estado"] == EstadoUsuario.SUSPENDIDO
    agent.refresh_from_db()
    assert not agent.is_active


@pytest.mark.django_db
def test_un_patch_vacio_responde_400(client, admin, agent):
    assert modificar(client, auth(client, admin.correo), agent).status_code == 400


@pytest.mark.django_db
def test_no_se_puede_bloquear_a_mano_desde_patch(client, admin, agent):
    respuesta = modificar(client, auth(client, admin.correo), agent, estado=EstadoUsuario.BLOQUEADO)

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_el_ultimo_administrador_no_puede_cambiar_de_rol(client, admin, agent_role):
    respuesta = modificar(client, auth(client, admin.correo), admin, rol=Rol.AGENTE_N1)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_administradores"
    admin.refresh_from_db()
    assert admin.rol_id == Rol.ADMINISTRADOR


@pytest.mark.django_db
def test_el_ultimo_administrador_no_puede_suspenderse(client, admin):
    respuesta = modificar(
        client, auth(client, admin.correo), admin, estado=EstadoUsuario.SUSPENDIDO
    )

    assert respuesta.status_code == 403
    admin.refresh_from_db()
    assert admin.estado == EstadoUsuario.ACTIVO


@pytest.mark.django_db
def test_con_otro_administrador_activo_si_se_permite(client, admin, admin_role, agent_role):
    Usuario.objects.create_user(
        correo="segundo@empresa-demo.mx", password=PASSWORD, nombre="Dos", rol=admin_role
    )

    respuesta = modificar(client, auth(client, admin.correo), admin, rol=Rol.AGENTE_N1)

    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_reactivar_limpia_los_intentos_fallidos(client, admin, agent):
    agent.estado = EstadoUsuario.SUSPENDIDO
    agent.intentos_fallidos = 2
    agent.save(update_fields=["estado", "intentos_fallidos"])

    modificar(client, auth(client, admin.correo), agent, estado=EstadoUsuario.ACTIVO)

    agent.refresh_from_db()
    assert agent.intentos_fallidos == 0


# --- POST /usuarios/{id}/desbloquear -----------------------------------------


@pytest.mark.django_db
def test_desbloquear_devuelve_la_cuenta_a_activo(client, admin, agent):
    agent.estado = EstadoUsuario.BLOQUEADO
    agent.intentos_fallidos = 3
    agent.save(update_fields=["estado", "intentos_fallidos"])

    respuesta = client.post(f"{USUARIOS}/{agent.id}/desbloquear", **auth(client, admin.correo))

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == EstadoUsuario.ACTIVO
    agent.refresh_from_db()
    assert agent.intentos_fallidos == 0
    assert agent.bloqueado_hasta is None


@pytest.mark.django_db
def test_un_usuario_final_no_puede_desbloquear(client, end_user, agent):
    respuesta = client.post(f"{USUARIOS}/{agent.id}/desbloquear", **auth(client, end_user.correo))

    assert respuesta.status_code == 403
