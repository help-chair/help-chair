"""Registro en el admin de Django, para revisar los datos sin escribir SQL."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Departamento, Perfil, Rol, Usuario


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "permisos")
    search_fields = ("id", "nombre")


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    extra = 0


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    inlines = [PerfilInline]
    list_display = ("correo", "nombre", "rol", "departamento", "estado")
    list_filter = ("estado", "rol", "departamento")
    search_fields = ("correo", "nombre")
    ordering = ("correo",)
    readonly_fields = ("date_joined", "last_login")
    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        ("Datos", {"fields": ("nombre", "rol", "departamento")}),
        ("Acceso", {"fields": ("estado", "intentos_fallidos", "bloqueado_hasta")}),
        ("Permisos", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("correo", "nombre", "rol", "password1", "password2"),
            },
        ),
    )
