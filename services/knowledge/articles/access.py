"""Único punto de autorización de la API de artículos (provisional hasta el JWT de Accesos, D-29).

El contrato distingue al usuario final (solo ``publicado`` + ``empresa``) del soporte autorizado
(otros estados y audiencia ``soporte``; único que crea y edita borradores) y toma ``autor_id`` del
``sub`` validado. Validar ese JWT depende de Accesos (D-29, bloqueado), así que hoy:

- no hay autenticación (``DEFAULT_AUTHENTICATION_CLASSES = []``): ni la sesión del admin ni
  Basic Auth identifican a nadie en la API;
- toda solicitud se trata como soporte autorizado: ve todos los artículos y puede editar;
- ``autor_id`` queda en ``null`` en los borradores creados por la API.

Cuando llegue el JWT solo cambia este módulo: la vista ya aplica ``visible_articles`` antes de
cualquier filtro (ningún filtro amplía la audiencia) y responde 404 a un artículo no visible.
"""

from rest_framework.permissions import BasePermission


class ArticlePermission(BasePermission):
    """Permiso de las operaciones de artículos. Provisional: permite todo (sin JWT, D-29).

    Con el JWT: 401 sin credencial válida y 403 (``no_permitido``) si el principal no puede crear
    o editar borradores.
    """

    def has_permission(self, request, view):
        return True


def visible_articles(request, queryset):
    """Artículos que el principal puede ver. Provisional: todos, como soporte autorizado.

    Con el JWT, un usuario final verá solo ``status=publicado`` y ``visibility=empresa``.
    """
    return queryset


def author_id_for(request):
    """UUID de Accesos del autor de un borrador nuevo. Provisional: ``None`` hasta tener ``sub``.

    Nunca se toma del cuerpo ni del usuario staff local (``request.user``).
    """
    return None
