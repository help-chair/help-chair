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