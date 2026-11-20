"""Permisos por rol para los endpoints del servicio.

Los consumidores preguntan por **permiso**, no por rol: así agregar un rol nuevo
no obliga a tocar cada endpoint. Los permisos viajan en el claim ``permisos`` del
token, de modo que comprobarlos no cuesta una consulta a la base.

Uso en una vista:

    from .models import Permiso
    from .permissions import requiere

    class UsuariosView(APIView):
        permission_classes = [requiere(Permiso.USUARIOS_ADMINISTRAR)]

Con varios permisos basta **uno** de ellos (``requiere(A, B)`` es «A o B»). Para
exigir los dos, se encadenan dos clases: ``[requiere(A), requiere(B)]``.
"""

from rest_framework.permissions import BasePermission

MENSAJE = "Tu rol no tiene permiso para esta operación."


def permisos_de(request) -> set[str]:
    """Permisos de quien hace la petición.

    Se leen del token, que es la fuente que usan los demás servicios. Si la
    petición no trae token pero sí sesión de Django (el admin, por ejemplo), se
    cae al rol del usuario en la base.
    """
    token = getattr(request, "auth", None)
    if token is not None:
        try:
            del_token = token["permisos"]
        except (KeyError, TypeError):
            del_token = None
        if del_token is not None:
            return set(del_token)

    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return set()
    return set(getattr(usuario, "permisos", []) or [])


def requiere(*permisos_necesarios: str) -> type[BasePermission]:
    """Clase de permiso que exige al menos uno de los permisos indicados."""
    necesarios = {str(permiso) for permiso in permisos_necesarios}

    class PermisoRequerido(BasePermission):
        message = MENSAJE

        def has_permission(self, request, view) -> bool:
            usuario = getattr(request, "user", None)
            if usuario is None or not usuario.is_authenticated:
                return False
            return bool(permisos_de(request) & necesarios)

    PermisoRequerido.__name__ = "Requiere_" + "_".join(
        sorted(p.replace(":", "_") for p in necesarios)
    )
    return PermisoRequerido
