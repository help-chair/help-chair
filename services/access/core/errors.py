"""Forma única de los errores de la API: ``{codigo, detalle, campos}``.

Es la que declara ``contracts/access/openapi.yaml`` y la que ya lee
``frontend/src/api/client.ts``. Django REST Framework devolvería
``{"detail": "..."}`` y SimpleJWT escribe sus mensajes en inglés, así que este
manejador traduce ambos antes de responder.

Se conecta en ``config/settings.py`` con ``REST_FRAMEWORK["EXCEPTION_HANDLER"]``.
"""

from rest_framework import serializers
from rest_framework.views import exception_handler as manejador_de_drf

# Código por omisión según el estado HTTP, cuando la excepción no trae uno propio.
CODIGOS_POR_ESTADO = {
    400: "datos_invalidos",
    401: "credenciales_invalidas",
    403: "permiso_denegado",
    404: "no_encontrado",
    405: "metodo_no_permitido",
    409: "conflicto",
    415: "tipo_no_soportado",
    422: "datos_invalidos",
    423: "cuenta_bloqueada",
    429: "demasiadas_solicitudes",
}

# Los códigos de DRF y de SimpleJWT, traducidos al vocabulario del contrato.
CODIGOS_TRADUCIDOS = {
    "no_active_account": "credenciales_invalidas",
    "authentication_failed": "credenciales_invalidas",
    "token_not_valid": "token_invalido",
    "not_authenticated": "no_autenticado",
    "permission_denied": "permiso_denegado",
    "invalid": "datos_invalidos",
    # El token es válido pero su usuario ya no sirve: para quien llama, da igual.
    "user_not_found": "token_invalido",
    "user_inactive": "token_invalido",
}

# SimpleJWT trae sus mensajes en inglés y no siempre los traduce. Se cambian por
# coincidencia exacta, para no pisar los mensajes propios del servicio.
MENSAJES_TRADUCIDOS = {
    "No active account found with the given credentials": "Correo o contraseña incorrectos.",
    "Token is invalid or expired": "El token es inválido o ya expiró.",
    "Token is invalid": "El token es inválido o ya expiró.",
    "Given token not valid for any token type": "El token es inválido o ya expiró.",
}

MENSAJE_DE_CAMPOS = "Revisa los campos marcados."


def _texto(valor) -> str:
    """Aplana la lista de mensajes que DRF guarda por campo en una sola cadena."""
    if isinstance(valor, list | tuple):
        return " ".join(_texto(elemento) for elemento in valor)
    if isinstance(valor, dict):
        return " ".join(_texto(elemento) for elemento in valor.values())
    return str(valor)


def _codigo_de(exc, estado: int) -> str:
    """Código propio de la excepción, o el que corresponda al estado HTTP.

    DRF lo guarda como atributo ``code`` del detalle. SimpleJWT, en cambio,
    envuelve el detalle en ``{"detail": ..., "code": ...}``, así que hay que
    buscarlo también dentro del diccionario.
    """
    detalle = getattr(exc, "detail", None)
    codigo = getattr(detalle, "code", None)
    if codigo is None and isinstance(detalle, dict):
        codigo = detalle.get("code")
    return str(codigo) if codigo else CODIGOS_POR_ESTADO.get(estado, "error")


def manejador_de_errores(exc, context):
    respuesta = manejador_de_drf(exc, context)
    if respuesta is None:
        # No es una excepción de DRF: que la maneje Django y devuelva 500.
        return None

    codigo = _codigo_de(exc, respuesta.status_code)
    codigo = CODIGOS_TRADUCIDOS.get(codigo, codigo)

    campos: dict[str, str] = {}
    datos = respuesta.data

    if isinstance(datos, dict):
        if "detail" in datos:
            detalle = _texto(datos["detail"])
        else:
            campos = {nombre: _texto(valor) for nombre, valor in datos.items()}
            # DRF mete en non_field_errors lo que no pertenece a un campo concreto.
            generales = campos.pop("non_field_errors", "")
            detalle = generales or MENSAJE_DE_CAMPOS
    else:
        detalle = _texto(datos)

    detalle = MENSAJES_TRADUCIDOS.get(detalle.strip(), detalle)

    cuerpo: dict[str, object] = {"codigo": codigo, "detalle": detalle}
    if campos:
        cuerpo["campos"] = campos

    respuesta.data = cuerpo
    return respuesta


class ErrorSerializer(serializers.Serializer):
    """Solo documenta la forma del error; la arma ``manejador_de_errores``.

    Existe para que ``make openapi`` genere las respuestas de error y el esquema
    del código declare los mismos códigos HTTP que el contrato.
    """

    codigo = serializers.CharField()
    detalle = serializers.CharField()
    campos = serializers.DictField(child=serializers.CharField(), required=False)
