"""Filtros por query string validados a mano contra los ``TextChoices`` del modelo."""

from django.db import models
from rest_framework.exceptions import ValidationError


def filter_by_choices(
    queryset, query_params, choices_by_field: dict[str, type[models.TextChoices]]
):
    """Aplica ``campo=valor`` por cada filtro presente; un valor fuera de las opciones es un 400."""
    errors = {}
    for field, choices in choices_by_field.items():
        if field not in query_params:
            continue
        value = query_params.get(field)
        if value not in choices.values:
            errors[field] = f'"{value}" no es una opción válida.'
            continue
        queryset = queryset.filter(**{field: value})
    if errors:
        raise ValidationError(errors)
    return queryset
