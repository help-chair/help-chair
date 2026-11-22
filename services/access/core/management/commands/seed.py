"""Carga los datos fijos del servicio: el catálogo de roles y sus permisos.

Se ejecuta con `make seed`. Es idempotente: correrlo dos veces no duplica nada.
Los identificadores y los permisos son los que declara
`contracts/access/openapi.yaml`.
"""

from django.core.management.base import BaseCommand

from core.models import Permiso, Rol

ROLES = [
    {
        "id": Rol.ADMINISTRADOR,
        "nombre": "Administrador",
        "descripcion": "Configura la empresa y administra usuarios.",
        "permisos": [
            Permiso.TICKETS_VER,
            Permiso.TICKETS_ATENDER,
            Permiso.TICKETS_ESCALAR,
            Permiso.EMPRESA_CONFIGURAR,
            Permiso.USUARIOS_ADMINISTRAR,
        ],
    },
    {
        "id": Rol.AGENTE_N2,
        "nombre": "Agente N2",
        "descripcion": "Atiende lo escalado y participa en problemas.",
        "permisos": [
            Permiso.TICKETS_VER,
            Permiso.TICKETS_ATENDER,
            Permiso.TICKETS_ESCALAR,
        ],
    },
    {
        "id": Rol.AGENTE_N1,
        "nombre": "Agente N1",
        "descripcion": "Primera línea del Service Desk.",
        "permisos": [
            Permiso.TICKETS_VER,
            Permiso.TICKETS_ATENDER,
            Permiso.TICKETS_ESCALAR,
        ],
    },
    {
        "id": Rol.USUARIO_FINAL,
        "nombre": "Usuario final",
        "descripcion": "Levanta peticiones y consulta las suyas.",
        "permisos": [Permiso.TICKETS_VER],
    },
]


class Command(BaseCommand):
    help = "Carga el catálogo de roles del servicio access."

    def handle(self, *args, **opciones):
        for datos in ROLES:
            rol, creado = Rol.objects.update_or_create(
                id=datos["id"],
                defaults={
                    "nombre": datos["nombre"],
                    "descripcion": datos["descripcion"],
                    "permisos": [str(p) for p in datos["permisos"]],
                },
            )
            verbo = "creado" if creado else "actualizado"
            self.stdout.write(f"  rol {rol.id}: {verbo}")
        self.stdout.write(self.style.SUCCESS(f"{len(ROLES)} roles listos."))
