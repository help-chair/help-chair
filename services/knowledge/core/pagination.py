"""Paginación común de las listas del servicio (``page``/``page_size`` del contrato)."""

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """``page`` (desde 1) y ``page_size`` (20 por defecto, máximo 100).

    Un ``page`` o ``page_size`` que no sea entero positivo es un 400; un ``page_size`` mayor que el
    máximo se recorta a 100. Una página fuera de rango es un 404, salvo la primera página vacía,
    que responde 200 con ``results`` vacío.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    invalid_page_message = "La página solicitada no existe."

    def paginate_queryset(self, queryset, request, view=None):
        errors = {}
        for param in (self.page_query_param, self.page_size_query_param):
            value = request.query_params.get(param)
            if value is not None and not _is_positive_integer(value):
                errors[param] = "Debe ser un número entero mayor o igual a 1."
        if errors:
            raise ValidationError(errors)
        return super().paginate_queryset(queryset, request, view)

    def get_schema_operation_parameters(self, view):
        parameters = super().get_schema_operation_parameters(view)
        limits = {
            self.page_query_param: {"minimum": 1, "default": 1},
            self.page_size_query_param: {
                "minimum": 1,
                "maximum": self.max_page_size,
                "default": self.page_size,
            },
        }
        for parameter in parameters:
            parameter["schema"].update(limits.get(parameter["name"], {}))
        return parameters


def _is_positive_integer(value: str) -> bool:
    return value.isascii() and value.isdigit() and int(value) >= 1
