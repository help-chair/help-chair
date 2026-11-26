"""Pruebas del publicador de la bandeja de salida.

Lo que importa aquí no es que el código corra, sino las tres garantías que pide
el #172: que el sobre cumpla el contrato que definió Eventos, que un evento no
se marque como publicado si el broker no lo confirmó, y que iniciar sesión no
dependa del broker para nada.

No hace falta NATS ni el paquete `nats-py`: el publicador es cualquier función
que reciba `(subject, cuerpo)`, así que aquí se le pasa una de mentiras.
"""

import json

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from jsonschema import Draft202012Validator

from core import outbox
from core.models import OutboxMessage, Permiso, Rol

LOGIN = "/api/access/v1/login"
CORREO = "lucia@empresa-demo.mx"
CLAVE = "clave-de-prueba-123"

Usuario = get_user_model()


@pytest.fixture
def esquema_del_sobre():
    """El contrato de verdad, no una copia: si cambia, estas pruebas se enteran."""
    ruta = settings.BASE_DIR.parent.parent / "contracts" / "messages" / "event-envelope.json"
    return Draft202012Validator(json.loads(ruta.read_text(encoding="utf-8")))


@pytest.fixture
def usuario(db):
    rol = Rol.objects.create(
        id=Rol.USUARIO_FINAL, nombre="Usuario final", permisos=[Permiso.TICKETS_VER]
    )
    return Usuario.objects.create_user(correo=CORREO, password=CLAVE, nombre="Lucía Mena", rol=rol)


@pytest.fixture
def mensaje(db):
    return OutboxMessage.objects.create(
        type="access.login.exitoso",
        payload={"usuario_id": "u-1", "rol": "usuario_final", "ip": "10.0.0.7"},
        occurred_at=timezone.now(),
    )


class PublicadorDeMentiras:
    """Guarda lo que le mandan. Con `falla=True` se hace el caído."""

    def __init__(self, falla: bool = False):
        self.falla = falla
        self.enviados: list[tuple[str, bytes]] = []

    def __call__(self, subject: str, cuerpo: bytes) -> None:
        if self.falla:
            raise ConnectionError("el broker no responde")
        self.enviados.append((subject, cuerpo))


def test_el_sobre_cumple_el_contrato_de_eventos(mensaje, esquema_del_sobre):
    esquema_del_sobre.validate(outbox.sobre(mensaje))


def test_el_sobre_lleva_el_id_del_mensaje_como_clave_de_idempotencia(mensaje):
    assert outbox.sobre(mensaje)["id"] == str(mensaje.id)
    assert outbox.sobre(mensaje)["origin"] == "access"


def test_publica_en_el_subject_del_tipo(mensaje):
    publicador = PublicadorDeMentiras()
    outbox.publicar_pendientes(publicador)

    subject, cuerpo = publicador.enviados[0]
    assert subject == "access.login.exitoso"
    assert json.loads(cuerpo)["payload"]["ip"] == "10.0.0.7"


def test_marca_lo_publicado_y_no_lo_vuelve_a_mandar(mensaje):
    publicador = PublicadorDeMentiras()

    assert outbox.publicar_pendientes(publicador) == (1, 0)
    mensaje.refresh_from_db()
    assert mensaje.published_at is not None

    # Segundo pase: ya no queda nada pendiente.
    assert outbox.publicar_pendientes(publicador) == (0, 0)
    assert len(publicador.enviados) == 1


def test_si_el_broker_no_confirma_el_evento_sigue_pendiente(mensaje):
    publicados, fallidos = outbox.publicar_pendientes(PublicadorDeMentiras(falla=True))

    assert (publicados, fallidos) == (0, 1)
    mensaje.refresh_from_db()
    assert mensaje.published_at is None, "no se puede dar por publicado lo que nadie recibió"


def test_respeta_el_tamano_del_lote(db):
    for _ in range(5):
        OutboxMessage.objects.create(type="access.login.fallido", occurred_at=timezone.now())

    publicador = PublicadorDeMentiras()
    assert outbox.publicar_pendientes(publicador, lote=2) == (2, 0)
    assert OutboxMessage.objects.filter(published_at__isnull=True).count() == 3


def test_iniciar_sesion_deja_su_evento_sin_tocar_el_broker(client, usuario):
    """La garantía del #172: el login no se cae si el broker no responde."""
    respuesta = client.post(
        LOGIN, {"correo": CORREO, "password": CLAVE}, content_type="application/json"
    )

    assert respuesta.status_code == 200
    evento = OutboxMessage.objects.get(type="access.login.exitoso")
    assert evento.published_at is None
    assert evento.payload["usuario_id"] == str(usuario.id)
