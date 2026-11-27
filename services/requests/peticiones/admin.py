from django.contrib import admin

from .models import Peticion, ServicioSolicitable


@admin.register(ServicioSolicitable)
class ServicioSolicitableAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


@admin.register(Peticion)
class PeticionAdmin(admin.ModelAdmin):
    list_display = [
        "titulo",
        "tipo",
        "servicio",
        "estado",
        "solicitante_id",
        "asignado_a_id",
        "creada",
    ]
    list_filter = ["estado", "tipo", "servicio"]
    search_fields = ["titulo", "descripcion"]