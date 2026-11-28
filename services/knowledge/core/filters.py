"""Filtros por query string validados a mano: opciones (``TextChoices``) y códigos con patrón."""

import re

from django.db import models
from rest_framework.exceptions import ValidationError


def filter_by_choices(
    queryset, query_params, filters: dict[str, tuple[str, type[models.TextChoices]]]
):
    """Aplica ``param=valor`` sobre el campo del modelo; un valor fuera de las opciones es un 400.

    ``filters`` asocia cada parámetro público con ``(campo del modelo, choices)``.
    """
    errors = {}
    for param, (field, choices) in filters.items():
        if param not in query_params:
            continue
        value = query_params.get(param)
        if value not in choices.values:
            errors[param] = f'"{value}" no es una opción válida.'
            continue
        queryset = queryset.filter(**{field: value})
    if errors:
        raise ValidationError(errors)
    return queryset


def filter_by_pattern(queryset, query_params, filters: dict[str, tuple[str, re.Pattern, str]]):
    """Aplica ``param=valor`` exacto si el valor cumple el patrón completo; si no, 400.

    ``filters`` asocia cada parámetro con ``(campo del modelo, patrón, mensaje de error)``. Un
    valor válido que no existe no es un error: simplemente no hay coincidencias.
    """
    errors = {}
    for param, (field, pattern, message) in filters.items():
        if param not in query_params:
            continue
        value = query_params.get(param)
        if not pattern.fullmatch(value):
            errors[param] = message
            continue
        queryset = queryset.filter(**{field: value})
    if errors:
        raise ValidationError(errors)
    return queryset
