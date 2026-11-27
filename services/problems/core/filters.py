"""Filtros por query string validados a mano: opciones, booleanos y búsqueda por texto."""

from django.db import models
from django.db.models import Q
from rest_framework.exceptions import ValidationError


def filter_by_choices(
    queryset,
    query_params,
    filters: dict[str, tuple[str, type[models.TextChoices]]],
):
    """Aplica ``parámetro=valor`` por cada filtro presente; un valor fuera de las opciones es 400.

    ``filters`` mapea el parámetro público (el del contrato) al campo del modelo y sus opciones.
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


# Los booleanos en query string se escriben como en JSON (OpenAPI, ``style: form``).
BOOLEAN_VALUES = {"true": True, "false": False}


def filter_by_boolean(queryset, query_params, filters: dict[str, str]):
    """Aplica ``parámetro=true|false``; ``filters`` mapea el parámetro público al campo."""
    errors = {}
    for param, field in filters.items():
        if param not in query_params:
            continue
        value = query_params.get(param)
        if value not in BOOLEAN_VALUES:
            errors[param] = f'"{value}" no es un booleano válido; usa true o false.'
            continue
        queryset = queryset.filter(**{field: BOOLEAN_VALUES[value]})
    if errors:
        raise ValidationError(errors)
    return queryset


def search_text(queryset, query_params, fields: tuple[str, ...], param: str = "q"):
    """Filtra por ``param`` contenido en cualquiera de ``fields``, sin distinguir mayúsculas.

    Un valor vacío o solo con espacios no filtra.
    """
    term = query_params.get(param, "").strip()
    if not term:
        return queryset
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__icontains": term})
    return queryset.filter(condition)
