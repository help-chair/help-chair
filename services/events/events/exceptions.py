from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import exception_handler


def _flatten_errors(detail, prefix=""):
    fields = {}

    if isinstance(detail, dict):
        for key, value in detail.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            fields.update(_flatten_errors(value, name))
    elif isinstance(detail, list):
        for index, value in enumerate(detail):
            name = f"{prefix}.{index}" if prefix else str(index)
            fields.update(_flatten_errors(value, name))
    else:
        fields[prefix or "non_field_errors"] = str(detail)

    return fields


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        fields = _flatten_errors(exc.detail)
        if response is None:
            return None
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        response.data = {
            "code": "validation_error",
            "detail": "Datos inválidos en la solicitud.",
            "fields": fields,
        }
        return response

    if isinstance(exc, NotFound):
        return response_from_not_found(response)

    return response


def response_from_not_found(response):
    if response is not None:
        response.status_code = status.HTTP_404_NOT_FOUND
        response.data = {
            "code": "not_found",
            "detail": str(response.data.get("detail", "Recurso no encontrado")),
        }
    return response
