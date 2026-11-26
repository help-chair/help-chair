"""Piezas de documentación OpenAPI (drf-spectacular) comunes a todas las vistas del servicio.

Solo describen el esquema: el cuerpo real de los errores lo produce ``core.errors``.
"""

from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    """Esquema ``Error`` del contrato: ``{codigo, detalle, campos?}``."""

    codigo = serializers.CharField(help_text="Código estable del error, p. ej. no_encontrado.")
    detalle = serializers.CharField(help_text="Mensaje legible en español.")
    campos = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        help_text="Errores por campo (400): {campo: mensaje}.",
    )


# Respuestas de error reutilizables, con las descripciones de contracts/problems/openapi.yaml.
INVALID_DATA = OpenApiResponse(ErrorSerializer, description="Datos inválidos")
NOT_FOUND = OpenApiResponse(ErrorSerializer, description="Recurso inexistente")
PAGE_OUT_OF_RANGE = OpenApiResponse(ErrorSerializer, description="Página fuera de rango")
