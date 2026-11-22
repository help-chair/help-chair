from django.contrib import admin

from .models import ErrorConocido, Problema, ProblemaIncidente


class ProblemaIncidenteInline(admin.TabularInline):
    model = ProblemaIncidente
    extra = 0
    readonly_fields = ["vinculado_en"]


class ErrorConocidoInline(admin.StackedInline):
    model = ErrorConocido
    extra = 0


@admin.register(Problema)
class ProblemaAdmin(admin.ModelAdmin):
    list_display = ["id", "titulo", "estado", "prioridad", "origen", "asignado_a_id", "creado_en"]
    list_filter = ["estado", "prioridad", "origen"]
    search_fields = ["titulo", "descripcion", "causa_raiz"]
    readonly_fields = ["creado_en", "actualizado_en"]
    inlines = [ProblemaIncidenteInline, ErrorConocidoInline]


@admin.register(ErrorConocido)
class ErrorConocidoAdmin(admin.ModelAdmin):
    list_display = ["id", "titulo", "problema", "activo", "articulo_kb_id", "creado_en"]
    list_filter = ["activo"]
    search_fields = ["titulo", "descripcion", "causa_raiz", "workaround"]
    readonly_fields = ["creado_en", "actualizado_en"]


@admin.register(ProblemaIncidente)
class ProblemaIncidenteAdmin(admin.ModelAdmin):
    list_display = ["id", "problema", "incidente_id", "vinculado_en"]
    search_fields = ["incidente_id"]
