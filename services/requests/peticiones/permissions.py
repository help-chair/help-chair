"""Matriz de autorización y permisos planificada para la Fase 3 (integración con Access).

Durante la Fase 2, los endpoints operan sin autenticación obligatoria para permitir
pruebas de contrato y desarrollo desacoplado, validando únicamente la integridad de
identificadores y transiciones de estado.

En la Fase 3, una vez habilitada la validación de tokens/identidad con `services/access`,
se aplicarán los siguientes permisos por rol:

- `catalog:manage` (Admin de catálogo):
  Crear, editar y activar/desactivar elementos en `/api/servicios/`.
- `requests:create` (Usuario autenticado / Sistema):
  Crear nuevas peticiones de tipo `servicio` o `cambio` en `/api/peticiones/`.
- `requests:assign` (Coordinador / Agente):
  Ejecutar `POST /api/peticiones/{id}/asignar/` y validar que `asignado_a_id` sea
  un agente activo.
- `requests:transition` (Agente asignado / Coordinador):
  Ejecutar `POST /api/peticiones/{id}/cambiar-estado/` (el solicitante solo puede
  cancelar o reabrir su propia petición).
- `changes:approve` (Aprobador designado en onboarding):
  Ejecutar `POST /api/peticiones/{id}/aprobar/` y `POST /api/peticiones/{id}/rechazar/`,
  verificando contra Access que el usuario coincida con `aprobador_id` y tenga el permiso.
"""

from rest_framework.permissions import AllowAny, BasePermission

PHASE3_PERMISSION_MATRIX: dict[str, str] = {
    "catalog.manage": "Administrador de catálogo (CRUD de /api/servicios/)",
    "requests.create": "Usuario autenticado o servicio interno (POST /api/peticiones/)",
    "requests.assign": "Coordinador o agente activo (POST /api/peticiones/{id}/asignar/)",
    "requests.transition": "Agente asignado o solicitante para cancelar/reabrir",
    "changes.approve": "Aprobador autorizado en onboarding (aprobar/rechazar cambios)",
}


class Phase2OpenAccessPermission(BasePermission):
    """Permiso explícito para Fase 2: acceso abierto previo a integración con Access."""

    def has_permission(self, request, view) -> bool:
        return AllowAny().has_permission(request, view)