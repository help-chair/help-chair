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


# --- Pruebas de filtros en peticiones ---


def test_filtrar_peticiones(client, servicio, peticion):
    Peticion.objects.create(
        servicio=servicio,
        titulo="Acceso VPN",
        solicitante_id=2,
        asignado_a_id=9,
        estado=Peticion.Estado.ASIGNADO,
    )

    r_estado = client.get("/api/peticiones/?estado=asignado")
    assert r_estado.status_code == 200
    assert len(r_estado.json()) == 1
    assert r_estado.json()[0]["titulo"] == "Acceso VPN"

    r_asignado = client.get("/api/peticiones/?asignado_a_id=9")
    assert r_asignado.status_code == 200
    assert len(r_asignado.json()) == 1

    r_solicitante = client.get("/api/peticiones/?solicitante_id=1")
    assert r_solicitante.status_code == 200
    assert len(r_solicitante.json()) == 1
    assert r_solicitante.json()[0]["id"] == str(peticion.id)


def test_filtrar_peticiones_id_invalido(client):
    r = client.get("/api/peticiones/?asignado_a_id=no-es-numero")
    assert r.status_code == 400


# --- Pruebas de catálogo de servicios ---


def test_crear_y_editar_servicio(db, client):
    r_crear = client.post(
        "/api/servicios/",
        {"nombre": "Acceso a VPN", "descripcion": "Alta en red remota"},
        content_type="application/json",
    )
    assert r_crear.status_code == 201
    servicio_id = r_crear.json()["id"]

    r_editar = client.patch(
        f"/api/servicios/{servicio_id}/",
        {"descripcion": "Alta en VPN corporativa", "activo": False},
        content_type="application/json",
    )
    assert r_editar.status_code == 200
    assert r_editar.json()["activo"] is False

    # Oculto en el listado normal
    r_lista = client.get("/api/servicios/")
    assert r_lista.status_code == 200
    assert all(s["id"] != servicio_id for s in r_lista.json())

    # Visible al pedir incluir_inactivos=true y al consultar por ID
    r_todos = client.get("/api/servicios/?incluir_inactivos=true")
    assert any(s["id"] == servicio_id for s in r_todos.json())
    assert client.get(f"/api/servicios/{servicio_id}/").status_code == 200


def test_no_crear_peticion_con_servicio_inactivo(client, servicio):
    servicio.activo = False
    servicio.save()

    r = client.post(
        "/api/peticiones/",
        {
            "servicio": servicio.id,
            "titulo": "Intento en servicio inactivo",
            "solicitante_id": 1,
        },
        content_type="application/json",
    )
    assert r.status_code == 400