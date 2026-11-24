from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _flatten_errors(detail, prefix=""):
    fields = {}

    if isinstance(detail, dict):
        for key, value in detail.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            fields.update(_flatten_errors(value, name))
    elif isinstance(detail, list):
        if all(not isinstance(item, dict | list) for item in detail):
            # Lista de mensajes de un mismo campo: "title": "Este campo es obligatorio."
            fields[prefix or "non_field_errors"] = " ".join(str(item) for item in detail)
        else:
            for index, value in enumerate(detail):
                name = f"{prefix}.{index}" if prefix else str(index)
                fields.update(_flatten_errors(value, name))
    else:
        fields[prefix or "non_field_errors"] = str(detail)

    return fields


def custom_exception_handler(exc, context):
    """Todos los errores salen como {code, detail, fields?} (contrato de Eventos)."""
    # Se importa aquí para no cargar los modelos al leer settings.py.
    from .services import EventConflict, TransitionValidationError

    if isinstance(exc, EventConflict):  # incluye InvalidTransition
        return Response({"code": exc.code, "detail": str(exc)}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, TransitionValidationError):
        return Response(
            {
                "code": "validation_error",
                "detail": "Datos inválidos en la solicitud.",
                "fields": exc.fields,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        response.data = {
            "code": "validation_error",
            "detail": "Datos inválidos en la solicitud.",
            "fields": _flatten_errors(exc.detail),
        }
        return response

    if response is not None and response.status_code == status.HTTP_404_NOT_FOUND:
        return response_from_not_found(response)

    if isinstance(exc, APIException) and isinstance(response.data, dict):
        codes = exc.get_codes()
        response.data = {
            "code": codes if isinstance(codes, str) else exc.default_code,
            "detail": str(response.data.get("detail", exc.default_detail)),
        }
    return response


def response_from_not_found(response):
    if response is not None:
        response.status_code = status.HTTP_404_NOT_FOUND
        response.data = {
            "code": "not_found",
            "detail": str(response.data.get("detail", "Recurso no encontrado")),
        }
        return response
