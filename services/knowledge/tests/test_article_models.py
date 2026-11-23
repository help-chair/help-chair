import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from articles.models import Articulo, Categoria

pytestmark = pytest.mark.django_db


@pytest.fixture
def categoria():
    return Categoria.objects.create(codigo="red", nombre="Red")


@pytest.fixture
def publicado(categoria):
    articulo = Articulo.objects.create()
    articulo.titulo = "Comprobar la conexión"
    articulo.contenido = "Contenido sintético de demostración."
    articulo.categoria = categoria
    articulo.autor_id = uuid.uuid4()  # Sujeto externo: no se crea ningún usuario local.
    articulo.publicado_en = timezone.now()
    articulo.estado = Articulo.Estado.PUBLICADO
    articulo.full_clean()
    articulo.save()
    return articulo


def test_borrador_incompleto_y_publicacion_con_referencia_externa(categoria):
    articulo = Articulo()
    articulo.full_clean()
    articulo.save()
    articulo.refresh_from_db()
    assert (articulo.titulo, articulo.contenido, articulo.categoria_id) == ("", "", None)
    assert articulo.estado == Articulo.Estado.BORRADOR
    assert articulo.visibilidad == Articulo.Visibilidad.SOPORTE
    articulo.estado = Articulo.Estado.PUBLICADO
    with pytest.raises(ValidationError) as error:
        articulo.full_clean()
    assert {"titulo", "contenido", "categoria", "autor_id", "publicado_en"} <= set(
        error.value.message_dict
    )


@pytest.mark.parametrize(
    ("cambios", "restriccion"),
    [
        ({"estado": "inventado"}, "kb_articulo_estado_valido"),
        ({"visibilidad": "publico"}, "kb_articulo_visibilidad_valida"),
        ({"titulo": ""}, "kb_articulo_publicacion_completa"),
        ({"titulo": " \t\n"}, "kb_articulo_publicacion_completa"),
        ({"contenido": ""}, "kb_articulo_publicacion_completa"),
        ({"contenido": "\t\n"}, "kb_articulo_publicacion_completa"),
        ({"categoria_id": None}, "kb_articulo_publicacion_completa"),
        ({"autor_id": None}, "kb_articulo_publicacion_completa"),
        ({"publicado_en": None}, "kb_articulo_publicacion_completa"),
        ({"estado": "archivado"}, "kb_articulo_archivo_consistente"),
    ],
)
def test_sql_rechaza_publicados_invalidos_sin_validacion_de_formulario(
    publicado, cambios, restriccion
):
    with pytest.raises(IntegrityError, match=restriccion), transaction.atomic():
        Articulo.objects.filter(pk=publicado.pk).update(**cambios)


@pytest.mark.parametrize(
    "caso", ["publicacion_anterior", "archivo_anterior", "archivo_sin_estado", "actualizacion"]
)
def test_sql_rechaza_fechas_y_archivo_incoherentes(publicado, caso):
    antes = publicado.creado_en - timedelta(seconds=1)
    cambios = {
        "publicacion_anterior": {"publicado_en": antes},
        "archivo_anterior": {"estado": "archivado", "archivado_en": publicado.creado_en},
        "archivo_sin_estado": {"archivado_en": timezone.now()},
        "actualizacion": {"actualizado_en": antes},
    }[caso]
    restriccion = (
        "kb_articulo_archivo_consistente"
        if caso == "archivo_sin_estado"
        else "kb_articulo_fechas_validas"
    )
    with pytest.raises(IntegrityError, match=restriccion), transaction.atomic():
        Articulo.objects.filter(pk=publicado.pk).update(**cambios)


@pytest.mark.parametrize("codigo", ["", "Red", "1red", "red-externa", "red\n", " red", "red "])
def test_categoria_codigo_invalido_en_validacion_y_sql(codigo):
    with pytest.raises(ValidationError):
        Categoria(codigo=codigo, nombre="Red").full_clean()
    with pytest.raises(IntegrityError, match="kb_categoria_codigo_valido"), transaction.atomic():
        Categoria.objects.create(codigo=codigo, nombre="Red")


@pytest.mark.parametrize("nombre", ["", " \t\n"])
def test_categoria_nombre_no_blanco_en_validacion_y_sql(nombre):
    with pytest.raises(ValidationError):
        Categoria(codigo="red", nombre=nombre).full_clean()
    with pytest.raises(IntegrityError, match="kb_categoria_nombre_no_blanco"), transaction.atomic():
        Categoria.objects.create(codigo="red", nombre=nombre)


def test_fk_local_impide_categoria_inexistente():
    with pytest.raises(IntegrityError), transaction.atomic():
        Articulo.objects.create(categoria_id="inexistente")
        # Las FK diferibles de PostgreSQL también deben comprobarse dentro del savepoint.
        connection.check_constraints()


@pytest.mark.parametrize("campo,limite", [("codigo", 50), ("nombre", 100)])
def test_limites_de_categoria_en_validacion_y_postgresql(campo, limite):
    datos = {"codigo": "red", "nombre": "Red", campo: "a" * limite}
    categoria = Categoria(**datos)
    categoria.full_clean()
    categoria.save()
    setattr(categoria, campo, "a" * (limite + 1))
    with pytest.raises(ValidationError):
        categoria.full_clean()
    if connection.vendor == "postgresql":
        with pytest.raises(DataError), transaction.atomic():
            Categoria.objects.filter(pk=datos["codigo"]).update(**{campo: "a" * (limite + 1)})


def test_limite_del_titulo_acordado(publicado):
    publicado.titulo = "a" * 200
    publicado.full_clean()
    publicado.save()
    publicado.titulo += "a"
    with pytest.raises(ValidationError):
        publicado.full_clean()
    if connection.vendor == "postgresql":
        with pytest.raises(DataError), transaction.atomic():
            Articulo.objects.filter(pk=publicado.pk).update(titulo=publicado.titulo)


def test_archivo_conserva_identidad_y_categoria_protegida(publicado):
    identidad, contenido, fecha = publicado.pk, publicado.contenido, publicado.publicado_en
    with pytest.raises(ProtectedError):
        publicado.categoria.delete()
    publicado.estado = Articulo.Estado.ARCHIVADO
    publicado.archivado_en = timezone.now()
    publicado.full_clean()
    publicado.save()
    publicado.refresh_from_db()
    assert (publicado.pk, publicado.contenido, publicado.publicado_en) == (
        identidad,
        contenido,
        fecha,
    )


def test_categoria_inactiva_no_borra_publicados_y_se_valida_al_publicar(publicado):
    Categoria.objects.filter(pk=publicado.categoria_id).update(activa=False)
    assert Articulo.objects.get(pk=publicado.pk).estado == "publicado"
    with pytest.raises(ValidationError) as error:
        publicado.full_clean()
    assert "categoria" in error.value.message_dict


def test_titulos_iguales_no_se_convierten_en_unicidad_no_acordada(publicado):
    otro = Articulo.objects.create(titulo=publicado.titulo)
    assert otro.pk != publicado.pk


def test_fechas_invalidas_muestran_el_campo_en_validacion(publicado):
    publicado.publicado_en = publicado.creado_en - timedelta(days=1)
    with pytest.raises(ValidationError) as error:
        publicado.full_clean()
    assert "publicado_en" in error.value.message_dict


def test_fixture_canonica_se_puede_recargar_sin_duplicados():
    from django.core.management import call_command

    call_command("loaddata", "kb_demo", verbosity=0)
    antes = set(Articulo.objects.values_list("pk", flat=True))
    call_command("loaddata", "kb_demo", verbosity=0)
    assert Categoria.objects.count() == 2
    assert Articulo.objects.count() == 4
    assert set(Articulo.objects.values_list("pk", flat=True)) == antes
    for articulo in Articulo.objects.all():
        articulo.full_clean()
