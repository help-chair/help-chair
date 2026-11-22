import pytest
from django.db import IntegrityError, transaction

from problems.models import ErrorConocido, Problema, ProblemaIncidente

pytestmark = pytest.mark.django_db


def crear_problema(**kwargs):
    datos = {"titulo": "Caída del correo", "descripcion": "El correo falla cada lunes."}
    datos.update(kwargs)
    return Problema.objects.create(**datos)


def test_problema_valores_por_defecto():
    problema = crear_problema()

    assert problema.estado == Problema.Estado.REGISTRADO
    assert problema.prioridad == Problema.Prioridad.MEDIA
    assert problema.origen == Problema.Origen.MANUAL
    assert problema.causa_raiz == ""
    assert problema.asignado_a_id == ""
    assert problema.resuelto_en is None
    assert problema.creado_en is not None
    assert str(problema) == f"PRB-{problema.pk}: Caída del correo"


def test_error_conocido_con_workaround():
    problema = crear_problema(estado=Problema.Estado.ERROR_CONOCIDO)
    error = ErrorConocido.objects.create(
        problema=problema,
        titulo="Certificado SMTP vencido",
        descripcion="El servidor SMTP rechaza conexiones.",
        causa_raiz="El certificado TLS no se renueva automáticamente.",
        workaround="Reiniciar el servicio de correo tras renovar el certificado a mano.",
    )

    assert error.activo is True
    assert error.articulo_kb_id == ""
    assert error.workaround.startswith("Reiniciar")
    assert list(problema.errores_conocidos.all()) == [error]
    assert str(error) == f"KE-{error.pk}: Certificado SMTP vencido"


def test_no_se_puede_vincular_dos_veces_el_mismo_incidente():
    problema = crear_problema()
    ProblemaIncidente.objects.create(problema=problema, incidente_id="INC-1")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProblemaIncidente.objects.create(problema=problema, incidente_id="INC-1")

    assert problema.incidentes.count() == 1


def test_el_mismo_incidente_puede_vincularse_a_otro_problema():
    ProblemaIncidente.objects.create(problema=crear_problema(), incidente_id="INC-1")
    ProblemaIncidente.objects.create(problema=crear_problema(), incidente_id="INC-1")

    assert ProblemaIncidente.objects.filter(incidente_id="INC-1").count() == 2
