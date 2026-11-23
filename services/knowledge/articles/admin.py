from django.contrib import admin
from django.forms import ModelForm
from django.utils import timezone

from .models import Articulo, Categoria


class ArticuloAdminForm(ModelForm):
    class Meta:
        model = Articulo
        fields = ("titulo", "contenido", "categoria", "estado", "visibilidad", "autor_id")

    def clean(self):
        datos = super().clean()
        estado = datos.get("estado")
        if self.instance._state.adding and estado != Articulo.Estado.BORRADOR:
            self.add_error("estado", "Crea primero un borrador y luego completa su publicación.")
        elif estado:
            ahora = timezone.now()
            if estado == Articulo.Estado.PUBLICADO and self.instance.estado != estado:
                self.instance.publicado_en = ahora
            if estado == Articulo.Estado.ARCHIVADO:
                if self.instance.estado != estado:
                    self.instance.archivado_en = ahora
            else:
                self.instance.archivado_en = None
        return datos


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("codigo", "nombre")

    def get_readonly_fields(self, request, obj=None):
        return ("codigo", "creado_en", "actualizado_en") if obj else ("creado_en", "actualizado_en")


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    form = ArticuloAdminForm
    list_display = ("titulo", "id", "estado", "visibilidad", "categoria", "actualizado_en")
    list_filter = ("estado", "visibilidad", "categoria")
    search_fields = ("titulo", "contenido")
    readonly_fields = ("id", "creado_en", "actualizado_en", "publicado_en", "archivado_en")
    fields = (
        "id",
        "titulo",
        "contenido",
        "categoria",
        "estado",
        "visibilidad",
        "autor_id",
        "creado_en",
        "actualizado_en",
        "publicado_en",
        "archivado_en",
    )

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (("autor_id",) if obj and obj.autor_id else ())

    def has_delete_permission(self, request, obj=None):
        # No podemos saber qué otros servicios conservan una referencia a este UUID.
        return False
