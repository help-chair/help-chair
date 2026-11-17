"""Pruebas del login con JWT.

La respuesta usa los nombres del contrato (``acceso``, ``refresco``,
``token_tipo``, ``expira_en``, ``usuario``), no los de SimpleJWT.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Departamento, EstadoUsuario, Permiso, Rol

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


def _refrescar(client, refresco):
    return client.post(REFRESH, {"refresco": refresco}, content_type="application/json")


@pytest.mark.django_db
def test_login_entrega_la_sesion_del_contrato(client, usuario, settings):
    respuesta = _login(client)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["acceso"]
    assert cuerpo["refresco"]
    assert cuerpo["token_tipo"] == "Bearer"
    vigencia = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    assert cuerpo["expira_en"] == int(vigencia.total_seconds())
    # Los nombres en inglés de SimpleJWT no deben asomar: el frontend no los lee.
    assert "access" not in cuerpo
    assert "refresh" not in cuerpo


@pytest.mark.django_db
def test_la_sesion_trae_al_usuario_con_sus_permisos(client, usuario):
    sesion = _login(client).json()["usuario"]

    assert sesion["id"] == str(usuario.id)
    assert sesion["correo"] == CORREO
    assert sesion["nombre"] == "Ana Ruiz"
    assert sesion["rol"] == Rol.AGENTE_N1
    assert sesion["estado"] == EstadoUsuario.ACTIVO
    assert sesion["permisos"] == [Permiso.TICKETS_VER, Permiso.TICKETS_ATENDER]
    assert sesion["onboarding_completed"] is False
    assert sesion["departamento"] is None


@pytest.mark.django_db
def test_la_sesion_nombra_el_departamento_cuando_lo_hay(client, usuario):
    usuario.departamento = Departamento.objects.create(nombre="Sistemas")
    usuario.save(update_fields=["departamento"])

    assert _login(client).json()["usuario"]["departamento"] == "Sistemas"


@pytest.mark.django_db
def test_el_token_lleva_los_claims_del_contrato(client, usuario, settings):
    token = AccessToken(_login(client).json()["acceso"])

    assert token["empresa"] == settings.EMPRESA_ID
    assert token["rol"] == Rol.AGENTE_N1
    assert token["permisos"] == [Permiso.TICKETS_VER, Permiso.TICKETS_ATENDER]
    assert token["sub"] == str(usuario.id)
    assert token["exp"] > token["iat"]


@pytest.mark.django_db
def test_un_usuario_sin_rol_entra_como_usuario_final(client):
    Usuario.objects.create_user(correo="sin.rol@empresa-demo.mx", password=CLAVE)

    token = AccessToken(_login(client, correo="sin.rol@empresa-demo.mx").json()["acceso"])

    assert token["rol"] == Rol.USUARIO_FINAL
    assert token["permisos"] == []


@pytest.mark.django_db
def test_contrasena_incorrecta_devuelve_401_con_la_forma_del_contrato(client, usuario):
    respuesta = _login(client, clave="no-es-la-clave")

    assert respuesta.status_code == 401
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "credenciales_invalidas"
    assert cuerpo["detalle"]
    assert "detail" not in cuerpo


@pytest.mark.django_db
def test_usuario_inexistente_responde_lo_mismo_que_contrasena_mala(client, db):
    respuesta = _login(client, correo="nadie@empresa-demo.mx")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"


@pytest.mark.django_db
def test_un_invitado_recibe_403_y_no_401(client, usuario):
    usuario.estado = EstadoUsuario.INVITADO
    usuario.save(update_fields=["estado"])

    respuesta = _login(client)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "cuenta_no_activada"


@pytest.mark.django_db
def test_un_bloqueado_recibe_423(client, usuario):
    usuario.estado = EstadoUsuario.BLOQUEADO
    usuario.save(update_fields=["estado"])

    respuesta = _login(client)

    assert respuesta.status_code == 423
    assert respuesta.json()["codigo"] == "cuenta_bloqueada"


@pytest.mark.django_db
def test_un_suspendido_no_entra_y_no_se_delata(client, usuario):
    usuario.estado = EstadoUsuario.SUSPENDIDO
    usuario.save(update_fields=["estado"])

    respuesta = _login(client)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"


@pytest.mark.django_db
def test_login_sin_correo_marca_el_campo(client, db):
    respuesta = client.post(LOGIN, {"password": CLAVE}, content_type="application/json")

    assert respuesta.status_code == 400
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "datos_invalidos"
    assert "correo" in cuerpo["campos"]


@pytest.mark.django_db
def test_entrar_bien_limpia_los_intentos_fallidos(client, usuario):
    usuario.intentos_fallidos = 3
    usuario.save(update_fields=["intentos_fallidos"])

    _login(client)

    usuario.refresh_from_db()
    assert usuario.intentos_fallidos == 0


@pytest.mark.django_db
def test_refresh_entrega_una_sesion_nueva(client, usuario):
    refresco = _login(client).json()["refresco"]

    respuesta = _refrescar(client, refresco)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["acceso"]
    assert cuerpo["usuario"]["correo"] == CORREO


@pytest.mark.django_db
def test_el_token_refrescado_conserva_los_claims(client, usuario, settings):
    refresco = _login(client).json()["refresco"]

    token = AccessToken(_refrescar(client, refresco).json()["acceso"])

    assert token["empresa"] == settings.EMPRESA_ID
    assert token["rol"] == Rol.AGENTE_N1
    assert token["permisos"] == [Permiso.TICKETS_VER, Permiso.TICKETS_ATENDER]


@pytest.mark.django_db
def test_refresh_invalido_devuelve_401(client, db):
    respuesta = _refrescar(client, "token-inventado")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "token_invalido"


@pytest.mark.django_db
def test_refresh_sin_el_campo_devuelve_400(client, db):
    respuesta = client.post(REFRESH, {}, content_type="application/json")

    assert respuesta.status_code == 400
    assert respuesta.json()["codigo"] == "datos_invalidos"


@pytest.mark.django_db
def test_refresh_de_una_cuenta_suspendida_deja_de_servir(client, usuario):
    refresco = _login(client).json()["refresco"]
    usuario.estado = EstadoUsuario.SUSPENDIDO
    usuario.save(update_fields=["estado"])

    respuesta = _refrescar(client, refresco)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "token_invalido"
