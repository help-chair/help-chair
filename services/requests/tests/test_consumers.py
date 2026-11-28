import asyncio
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from peticiones.consumers import (
    SERVICIO_POR_DEFECTO,
    SOLICITANTE_SISTEMA_ID,
    EventoInvalidoError,
    procesar_evento_enrutado,
)
from peticiones.management.commands.consume_events import manejar_mensaje_crudo
from peticiones.models import Peticion, ServicioSolicitable


@pytest.mark.django_db
def test_procesar_evento_crea_peticion_con_servicio_existente():
    servicio = ServicioSolicitable.objects.create(nombre="Soporte Técnico")

    peticion, creada = procesar_evento_enrutado(
        {
            "evento_id": 501,
            "tipo": "access.cuenta.bloqueada",
            "titulo": "Cuenta bloqueada por intentos fallidos",
            "descripcion": "El usuario superó 5 intentos.",
            "servicio": "soporte técnico",
            "datos": {"usuario_id": 42, "intentos": 5},
        }
    )

    assert creada is True
    assert peticion.evento_id == 501
    assert peticion.servicio == servicio
    assert peticion.solicitante_id == 42
    assert peticion.estado == Peticion.Estado.NUEVO
    assert "access.cuenta.bloqueada" in peticion.descripcion


@pytest.mark.django_db
def test_procesar_evento_usa_servicio_y_solicitante_por_defecto():
    peticion, creada = procesar_evento_enrutado(
        {
            "id": 777,
            "tipo": "infra.disco.lleno",
        }
    )

    assert creada is True
    assert peticion.evento_id == 777
    assert peticion.solicitante_id == SOLICITANTE_SISTEMA_ID
    assert peticion.servicio.nombre == SERVICIO_POR_DEFECTO


@pytest.mark.django_db
def test_procesar_evento_es_idempotente_por_evento_id():
    payload = {"evento_id": 900, "tipo": "access.rol.asignado", "datos": {"usuario_id": 10}}

    primera, creada_1 = procesar_evento_enrutado(payload)
    segunda, creada_2 = procesar_evento_enrutado(payload)

    assert creada_1 is True
    assert creada_2 is False
    assert primera.id == segunda.id
    assert Peticion.objects.filter(evento_id=900).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload_invalido",
    [
        "no-es-un-dict",
        {},
        {"evento_id": "abc"},
        {"evento_id": 0},
        {"evento_id": True},
        {"evento_id": 10, "solicitante_id": -5},
    ],
)
def test_procesar_evento_rechaza_payload_invalido(payload_invalido):
    with pytest.raises(EventoInvalidoError):
        procesar_evento_enrutado(payload_invalido)


@pytest.mark.django_db(transaction=True)
def test_manejar_mensaje_crudo_ignora_basura_y_procesa_valido():
    asyncio.run(manejar_mensaje_crudo(b"{json-corrupto"))
    asyncio.run(manejar_mensaje_crudo(json.dumps({"sin_evento_id": True}).encode("utf-8")))
    assert Peticion.objects.count() == 0

    valido = json.dumps({"evento_id": 1234, "titulo": "Alerta de prueba"}).encode("utf-8")
    asyncio.run(manejar_mensaje_crudo(valido))
    assert Peticion.objects.filter(evento_id=1234).count() == 1


def test_consume_events_falla_si_no_hay_broker_url(settings):
    settings.BROKER_URL = ""
    with pytest.raises(CommandError, match="BROKER_URL"):
        call_command("consume_events")