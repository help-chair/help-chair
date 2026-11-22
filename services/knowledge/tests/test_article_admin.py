import uuid

import pytest
from django.urls import reverse

from articles.models import Articulo, Categoria

pytestmark = pytest.mark.django_db


def test_admin_guarda_borrador_sin_usar_staff_como_autor(admin_client):
    respuesta = admin_client.post(
        reverse("admin:articles_articulo_add"),
        {"titulo": "", "contenido": "", "estado": "borrador", "visibilidad": "soporte"},
    )
    assert respuesta.status_code == 302
    articulo = Articulo.objects.get()
    assert articulo.autor_id is None
    borrar = reverse("admin:articles_articulo_delete", args=[articulo.pk])
    assert admin_client.get(borrar).status_code == 403


def test_admin_muestra_errores_sin_guardar_publicado_incompleto(admin_client):
    articulo = Articulo.objects.create()
    respuesta = admin_client.post(
        reverse("admin:articles_articulo_change", args=[articulo.pk]),
        {"titulo": " \t", "contenido": "", "estado": "publicado", "visibilidad": "empresa"},
    )
    assert respuesta.status_code == 200
    assert "titulo" in respuesta.context["adminform"].form.errors
    articulo.refresh_from_db()
    assert articulo.estado == "borrador"


def test_admin_exige_borrador_inicial_y_gestiona_fechas_y_autor(admin_client):
    categoria = Categoria.objects.create(codigo="red", nombre="Red")
    autor = uuid.uuid4()
    datos = {
        "titulo": "Ejemplo",
        "contenido": "Datos sintéticos",
        "categoria": categoria.pk,
        "autor_id": str(autor),
        "estado": "publicado",
        "visibilidad": "empresa",
    }
    alta = reverse("admin:articles_articulo_add")
    assert "estado" in admin_client.post(alta, datos).context["adminform"].form.errors
    assert not Articulo.objects.exists()
    datos["estado"] = "borrador"
    assert admin_client.post(alta, datos).status_code == 302
    articulo = Articulo.objects.get()
    editar = reverse("admin:articles_articulo_change", args=[articulo.pk])
    datos.update(estado="publicado", autor_id=str(uuid.uuid4()), publicado_en_0="1900-01-01")
    assert admin_client.post(editar, datos).status_code == 302
    articulo.refresh_from_db()
    assert articulo.autor_id == autor  # El POST no puede sustituir el autor ya fijado.
    assert articulo.publicado_en >= articulo.creado_en
    fecha = articulo.publicado_en
    datos["estado"] = "archivado"
    assert admin_client.post(editar, datos).status_code == 302
    articulo.refresh_from_db()
    assert articulo.publicado_en == fecha
    assert articulo.archivado_en >= fecha
