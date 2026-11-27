"""Formato de error común de la API: ``{codigo, detalle, campos}`` (esquema ``Error`` del contrato).

Se registra en ``REST_FRAMEWORK["EXCEPTION_HANDLER"]`` y aplica a todas las vistas DRF del
servicio. El cuerpo nunca incluye texto de excepciones, DSN, cabeceras ni tokens.
"""

import logging
from collections.abc import Mapping

from django.db import InterfaceError, OperationalError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

# Valores de "codigo": los del contrato de KB y, para estados que no define, los de Problemas.
CODES_BY_STATUS = {
    status.HTTP_400_BAD_REQUEST: "datos_invalidos",
    status.HTTP_401_UNAUTHORIZED: "no_autenticado",
    status.HTTP_403_FORBIDDEN: "no_permitido",
    status.HTTP_404_NOT_FOUND: "no_encontrado",
    status.HTTP_405_METHOD_NOT_ALLOWED: "metodo_no_permitido",
    status.HTTP_406_NOT_ACCEPTABLE: "no_aceptable",
    status.HTTP_409_CONFLICT: "conflicto",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "tipo_no_soportado",
    status.HTTP_429_TOO_MANY_REQUESTS: "demasiadas_solicitudes",
    status.HTTP_503_SERVICE_UNAVAILABLE: "servicio_no_disponible",
}

INVALID_DATA_DETAIL = "La solicitud tiene campos inválidos."
NOT_FOUND_DETAIL = "Recurso no encontrado."
UNAVAILABLE_DETAIL = "Servicio temporalmente no disponible."
NON_FIELD_KEY = "non_field_errors"


class Conflict(exceptions.APIException):
    """409 con un código de negocio propio (p. ej. ``estado_no_editable``)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "La solicitud entra en conflicto con el estado actual del recurso."
    default_code = "conflicto"

    def __init__(self, detail: str | None = None, error_code: str | None = None):
        super().__init__(detail)
        self.error_code = error_code or self.default_code


def first_message(detail) -> str:
    """Devuelve el primer mensaje de un detalle de DRF (cadena, lista o diccionario anidado)."""
    if isinstance(detail, Mapping):
        return first_message(next(iter(detail.values()), ""))
    if isinstance(detail, list | tuple):
        return first_message(detail[0]) if detail else ""
    return str(detail)


def _validation_body(detail) -> dict:
    if not isinstance(detail, Mapping):
        return {"codigo": "datos_invalidos", "detalle": first_message(detail)}
    fields = {str(field): first_message(messages) for field, messages in detail.items()}
    general = fields.pop(NON_FIELD_KEY, None)
    body = {"codigo": "datos_invalidos", "detalle": general or INVALID_DATA_DETAIL}
    if fields:
        body["campos"] = fields
    return body


def handle_exception(exc, context):
    """Adapta la respuesta de DRF al esquema ``Error``; lo no previsto sigue siendo un 500.

    Una BD caída o inalcanzable es un 503, nunca una lista vacía ni un 500 con detalles.
    """
    if isinstance(exc, OperationalError | InterfaceError):
        # JsonFormatter publica solo el tipo de exc_info: el mensaje del driver puede llevar host
        # o usuario de la BD y no sale ni en el log ni en la respuesta.
        logger.warning("database_unavailable", exc_info=exc)
        return Response(
            {"codigo": CODES_BY_STATUS[503], "detalle": UNAVAILABLE_DETAIL},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if isinstance(exc, Http404):
        exc = exceptions.NotFound(NOT_FOUND_DETAIL)
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, exceptions.ValidationError):
        response.data = _validation_body(exc.detail)
        return response

    code = getattr(exc, "error_code", None) or CODES_BY_STATUS.get(response.status_code, "error")
    detail = getattr(exc, "detail", None)
    response.data = {"codigo": code, "detalle": first_message(detail) if detail else ""}
    return response
