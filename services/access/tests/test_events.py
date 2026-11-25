"""Pruebas de los eventos de seguridad que access deja en la bandeja de salida.

Los tipos vienen de `contracts/messages/access-eventos-seguridad.yaml` y el
sobre de `contracts/messages/event-envelope.json`. Aquí no se publica nada al
broker: se comprueba que el evento quede escrito y con la forma correcta.
"""

import pytest
from django.contrib.auth import get_user_model

from core import events
from core.models import EstadoUsuario, OutboxMessage, Permiso, Rol

LOGIN = "/api/access/v1/login"
CORREO = "ana@empresa-demo.mx"
PASSWORD = "clave-de-prueba-123"

Usuario = get_user_model()


@pytest.fixture
def usuario(db):
    rol = Rol.objects.create(
        id=Rol.AGENTE_N1, nombre="Agente N1", permisos=[Permiso.TICKETS_ATENDER]
    )
    return Usuario.objects.create_user(correo=CORREO, password=PASSWORD, nombre="Ana Ruiz", rol=rol)


def entrar(client, correo=CORREO, clave=PASSWORD, **extra):
    return client.post(
        LOGIN, {"correo": correo, "password": clave}, content_type="application/json", **extra
    )


def mensajes(tipo):
    return list(OutboxMessage.objects.filter(type=tipo))


# --- Login exitoso -----------------------------------------------------------


@pytest.mark.django_db
def test_entrar_bien_deja_el_evento(client, usuario):
    entrar(client)

    emitidos = mensajes(events.LOGIN_EXITOSO)
    assert len(emitidos) == 1
    assert emitidos[0].payload["usuario_id"] == str(usuario.id)
    assert emitidos[0].payload["rol"] == Rol.AGENTE_N1


@pytest.mark.django_db
def test_el_evento_guarda_la_ip_de_quien_entro(client, usuario):
    entrar(client, HTTP_X_FORWARDED_FOR="187.190.1.5, 10.0.0.1")

    assert mensajes(events.LOGIN_EXITOSO)[0].payload["ip"] == "187.190.1.5"


# --- Login fallido -----------------------------------------------------------


@pytest.mark.django_db
def test_una_clave_mala_deja_el_evento_con_el_conteo(client, usuario):
    entrar(client, clave="no-es")

    emitidos = mensajes(events.LOGIN_FALLIDO)
    assert len(emitidos) == 1
    assert emitidos[0].payload["identificador"] == CORREO
    assert emitidos[0].payload["intentos"] == 1


@pytest.mark.django_db
def test_un_correo_inventado_tambien_se_reporta(client, db):
    """No incrementa ningún contador, pero Eventos debe ver el intento."""
    entrar(client, correo="nadie@empresa-demo.mx", clave="mal")

    emitidos = mensajes(events.LOGIN_FALLIDO)
    assert len(emitidos) == 1
    assert emitidos[0].payload["identificador"] == "nadie@empresa-demo.mx"


@pytest.mark.django_db
def test_entrar_bien_no_deja_evento_de_fallo(client, usuario):
    entrar(client)

    assert mensajes(events.LOGIN_FALLIDO) == []


# --- Cuenta bloqueada --------------------------------------------------------


@pytest.mark.django_db
def test_al_bloquearse_la_cuenta_se_emite_el_evento(client, usuario, settings):
    settings.INTENTOS_ANTES_DE_BLOQUEAR = 3

    for _ in range(3):
        entrar(client, clave="mal")

    emitidos = mensajes(events.CUENTA_BLOQUEADA)
    assert len(emitidos) == 1
    assert emitidos[0].payload["usuario_id"] == str(usuario.id)
    assert emitidos[0].payload["intentos"] == 3
    usuario.refresh_from_db()
    assert usuario.estado == EstadoUsuario.BLOQUEADO


@pytest.mark.django_db
def test_no_se_bloquea_antes_de_tiempo(client, usuario, settings):
    settings.INTENTOS_ANTES_DE_BLOQUEAR = 3

    entrar(client, clave="mal")
    entrar(client, clave="mal")

    assert mensajes(events.CUENTA_BLOQUEADA) == []


# --- Forma del sobre ---------------------------------------------------------


@pytest.mark.django_db
def test_el_sobre_trae_lo_que_pide_el_contrato(client, usuario):
    entrar(client)

    sobre = mensajes(events.LOGIN_EXITOSO)[0].as_envelope()

    assert set(sobre) == {
        "id",
        "type",
        "version",
        "origin",
        "timestamp",
        "occurred_at",
        "payload",
    }
    assert sobre["origin"] == "access"
    assert sobre["type"] == "access.login.exitoso"
    assert sobre["version"] == 1


@pytest.mark.django_db
def test_el_mensaje_nace_sin_publicar(client, usuario):
    """El publicador al broker todavía no existe; la fila queda pendiente."""
    entrar(client)

    assert mensajes(events.LOGIN_EXITOSO)[0].published_at is None


@pytest.mark.django_db
def test_el_id_del_sobre_es_el_de_la_fila(client, usuario):
    """Es la clave de idempotencia que usan los consumidores."""
    entrar(client)

    fila = mensajes(events.LOGIN_EXITOSO)[0]
    assert fila.as_envelope()["id"] == str(fila.id)
