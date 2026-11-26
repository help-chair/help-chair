"""Filtros por query string validados a mano contra los ``TextChoices`` del modelo."""

from django.db import models
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
