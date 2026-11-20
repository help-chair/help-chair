import pytest

from peticiones.models import Peticion, ServicioSolicitable


@pytest.fixture
def servicio(db):
    return ServicioSolicitable.objects.create(nombre="Alta de correo")


@pytest.fixture
def peticion(servicio):
    return Peticion.objects.create(
        servicio=servicio,
        titulo="Necesito un correo nuevo",
        solicitante_id=1,
    )


def test_estado_inicial_es_nuevo(peticion):
    assert peticion.estado == Peticion.Estado.NUEVO


def test_transicion_valida(peticion):
    assert peticion.puede_pasar_a(Peticion.Estado.ASIGNADO)


def test_transicion_invalida(peticion):
    assert not peticion.puede_pasar_a(Peticion.Estado.CERRADO)


def test_cerrado_es_final(peticion):
    peticion.estado = Peticion.Estado.CERRADO
    assert not peticion.puede_pasar_a(Peticion.Estado.REABIERTO)

def _post(client, peticion, accion, datos):
    return client.post(
        f"/api/peticiones/{peticion.id}/{accion}/",
        datos,
        content_type="application/json",
    )


def test_cambiar_estado_valido(client, peticion):
    r = _post(client, peticion, "cambiar-estado", {"estado": "asignado"})
    assert r.status_code == 200
    assert r.json()["estado"] == "asignado"


def test_cambiar_estado_invalido(client, peticion):
    r = _post(client, peticion, "cambiar-estado", {"estado": "cerrado"})
    assert r.status_code == 400


def test_cancelar_exige_motivo(client, peticion):
    r = _post(client, peticion, "cambiar-estado", {"estado": "cancelado"})
    assert r.status_code == 400


def test_cancelar_con_motivo(client, peticion):
    datos = {"estado": "cancelado", "motivo_cancelacion": "Ya no se necesita"}
    r = _post(client, peticion, "cambiar-estado", datos)
    assert r.status_code == 200
    assert r.json()["motivo_cancelacion"] == "Ya no se necesita"


def test_cerrar_registra_fecha(client, peticion):
    peticion.estado = Peticion.Estado.RESUELTO
    peticion.save()
    r = _post(client, peticion, "cambiar-estado", {"estado": "cerrado"})
    assert r.status_code == 200
    assert r.json()["cerrada_en"] is not None


def test_asignar_pasa_a_asignado(client, peticion):
    r = _post(client, peticion, "asignar", {"asignado_a_id": 5})
    assert r.status_code == 200
    assert r.json()["asignado_a_id"] == 5
    assert r.json()["estado"] == "asignado"


def test_no_asignar_si_esta_cerrada(client, peticion):
    peticion.estado = Peticion.Estado.CERRADO
    peticion.save()
    r = _post(client, peticion, "asignar", {"asignado_a_id": 5})
    assert r.status_code == 400 