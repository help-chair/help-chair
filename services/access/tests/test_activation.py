"""Pruebas de `/activate` y `/internal/v1/bootstrap-admin`.

Son las dos mitades del mismo flujo: el aprovisionador crea al administrador sin
contraseña y recibe un token; con ese token la persona define su contraseña y a
partir de ahí puede entrar.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import ActivationToken, EstadoUsuario, Permiso, Rol

LOGIN = "/api/access/v1/login"
ACTIVATE = "/api/access/v1/activate"
BOOTSTRAP = "/internal/v1/bootstrap-admin"
SECRETO = "secreto-del-aprovisionador"
PASSWORD = "contrasena-larga-123"

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
def aprovisionador(settings):
    settings.PROVISIONER_TOKEN = SECRETO
    return {"HTTP_AUTHORIZATION": f"Bearer {SECRETO}"}


@pytest.fixture
def invitado(db, admin_role):
    return Usuario.objects.create_user(
        correo="val@empresa-demo.mx", nombre="Val Ortiz", rol=admin_role
    )


def activar(client, token, password=PASSWORD):
    return client.post(
        ACTIVATE, {"token": token, "password": password}, content_type="application/json"
    )


def dar_de_alta(client, cabeceras, **datos):
    cuerpo = {"nombre": "Val Ortiz", "correo": "val@empresa-demo.mx"}
    cuerpo.update(datos)
    return client.post(BOOTSTRAP, cuerpo, content_type="application/json", **cabeceras)


# --- POST /activate ----------------------------------------------------------


@pytest.mark.django_db
def test_el_token_valido_activa_la_cuenta(client, invitado, settings):
    _, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)

    respuesta = activar(client, token)

    assert respuesta.status_code == 204
    invitado.refresh_from_db()
    assert invitado.estado == EstadoUsuario.ACTIVO
    assert invitado.check_password(PASSWORD)


@pytest.mark.django_db
def test_despues_de_activar_la_persona_ya_puede_entrar(client, invitado, settings):
    _, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)
    activar(client, token)

    respuesta = client.post(
        LOGIN,
        {"correo": invitado.correo, "password": PASSWORD},
        content_type="application/json",
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["acceso"]


@pytest.mark.django_db
def test_no_hace_falta_sesion_para_activar(client, invitado, settings):
    """El endpoint es público: quien activa todavía no tiene token de sesión."""
    _, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)

    respuesta = activar(client, token)

    assert respuesta.status_code == 204


@pytest.mark.django_db
def test_un_token_inventado_responde_400(client, invitado):
    respuesta = activar(client, "esto-no-es-un-token")

    assert respuesta.status_code == 400
    invitado.refresh_from_db()
    assert invitado.estado == EstadoUsuario.INVITADO


@pytest.mark.django_db
def test_el_token_no_sirve_dos_veces(client, invitado, settings):
    _, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)
    activar(client, token)

    segunda = activar(client, token, password="otra-contrasena-456")

    assert segunda.status_code == 400
    invitado.refresh_from_db()
    assert invitado.check_password(PASSWORD)


@pytest.mark.django_db
def test_un_token_caducado_responde_400(client, invitado, settings):
    registro, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)
    registro.expires_at = timezone.now() - timedelta(minutes=1)
    registro.save(update_fields=["expires_at"])

    assert activar(client, token).status_code == 400


@pytest.mark.django_db
def test_emitir_un_token_nuevo_invalida_el_anterior(client, invitado, settings):
    _, viejo = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)
    _, nuevo = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)

    assert activar(client, viejo).status_code == 400
    assert activar(client, nuevo).status_code == 204


@pytest.mark.django_db
def test_la_contrasena_debe_tener_al_menos_12_caracteres(client, invitado, settings):
    _, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)

    respuesta = activar(client, token, password="corta123")

    assert respuesta.status_code == 400
    assert "password" in respuesta.json().get("campos", {})
    invitado.refresh_from_db()
    assert invitado.estado == EstadoUsuario.INVITADO


@pytest.mark.django_db
def test_activar_limpia_el_bloqueo_por_intentos(client, invitado, settings):
    invitado.estado = EstadoUsuario.BLOQUEADO
    invitado.intentos_fallidos = 3
    invitado.save(update_fields=["estado", "intentos_fallidos"])
    _, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)

    activar(client, token)

    invitado.refresh_from_db()
    assert invitado.estado == EstadoUsuario.ACTIVO
    assert invitado.intentos_fallidos == 0
    assert invitado.bloqueado_hasta is None


@pytest.mark.django_db
def test_del_token_solo_se_guarda_el_hash(client, invitado, settings):
    registro, token = ActivationToken.issue(invitado, settings.ACTIVACION_VIGENCIA_HORAS)

    assert registro.token_hash != token
    assert registro.token_hash == ActivationToken.hash_of(token)
    assert len(registro.token_hash) == 64


# --- POST /internal/v1/bootstrap-admin ---------------------------------------


@pytest.mark.django_db
def test_sin_token_del_aprovisionador_responde_401(client, admin_role):
    assert dar_de_alta(client, {}).status_code == 401


@pytest.mark.django_db
def test_con_un_token_equivocado_responde_401(client, admin_role, settings):
    settings.PROVISIONER_TOKEN = SECRETO

    respuesta = dar_de_alta(client, {"HTTP_AUTHORIZATION": "Bearer otro-secreto"})

    assert respuesta.status_code == 401
    assert Usuario.objects.count() == 0


@pytest.mark.django_db
def test_si_no_hay_secreto_configurado_el_endpoint_queda_cerrado(client, admin_role, settings):
    """Un stack mal configurado no debe aceptar a cualquiera."""
    settings.PROVISIONER_TOKEN = ""

    respuesta = dar_de_alta(client, {"HTTP_AUTHORIZATION": "Bearer "})

    assert respuesta.status_code == 401


@pytest.mark.django_db
def test_crea_al_administrador_invitado_y_entrega_el_token(client, admin_role, aprovisionador):
    respuesta = dar_de_alta(client, aprovisionador)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["token_activacion"]
    assert cuerpo["expira_en"]

    usuario = Usuario.objects.get(pk=cuerpo["usuario_id"])
    assert usuario.rol_id == Rol.ADMINISTRADOR
    assert usuario.estado == EstadoUsuario.INVITADO
    assert not usuario.has_usable_password()


@pytest.mark.django_db
def test_el_segundo_intento_responde_409_y_no_crea_nada(client, admin_role, aprovisionador):
    dar_de_alta(client, aprovisionador)

    segunda = dar_de_alta(client, aprovisionador, correo="otro@empresa-demo.mx")

    assert segunda.status_code == 409
    assert Usuario.objects.count() == 1


@pytest.mark.django_db
def test_un_correo_mal_escrito_responde_422(client, admin_role, aprovisionador):
    respuesta = dar_de_alta(client, aprovisionador, correo="no-es-correo")

    assert respuesta.status_code == 422
    assert Usuario.objects.count() == 0


@pytest.mark.django_db
def test_sin_catalogo_de_roles_lo_dice_en_vez_de_tronar(client, db, aprovisionador):
    respuesta = dar_de_alta(client, aprovisionador)

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "catalogo_incompleto"


@pytest.mark.django_db
def test_el_flujo_completo_deja_al_administrador_dentro(client, admin_role, aprovisionador):
    alta = dar_de_alta(client, aprovisionador).json()

    activar(client, alta["token_activacion"])
    sesion = client.post(
        LOGIN,
        {"correo": "val@empresa-demo.mx", "password": PASSWORD},
        content_type="application/json",
    )

    assert sesion.status_code == 200
    assert sesion.json()["usuario"]["rol"] == Rol.ADMINISTRADOR
