"""Manejador de errores común (core.errors), independiente de un endpoint concreto."""

from django.http import Http404
from rest_framework import exceptions

from core.errors import Conflict, first_message, handle_exception


def body(exc):
    return handle_exception(exc, {}).data


def test_field_validation_uses_the_first_message_as_text():
    exc = exceptions.ValidationError({"titulo": ["Uno.", "Dos."], "otro": {"anidado": ["Tres."]}})
    assert body(exc) == {
        "codigo": "datos_invalidos",
        "detalle": "La solicitud tiene campos inválidos.",
        "campos": {"titulo": "Uno.", "otro": "Tres."},
    }


def test_general_validation_goes_in_detalle_without_campos():
    assert body(exceptions.ValidationError("Algo general.")) == {
        "codigo": "datos_invalidos",
        "detalle": "Algo general.",
    }
    assert body(exceptions.ValidationError({"non_field_errors": ["Combinación inválida."]})) == {
        "codigo": "datos_invalidos",
        "detalle": "Combinación inválida.",
    }


def test_django_http404_is_translated_to_the_error_schema():
    assert body(Http404("interno")) == {
        "codigo": "no_encontrado",
        "detalle": "No existe el recurso solicitado.",
    }


def test_conflict_carries_its_business_code():
    response = handle_exception(Conflict("Ya vinculado.", error_code="incidente_ya_vinculado"), {})
    assert response.status_code == 409
    assert response.data == {"codigo": "incidente_ya_vinculado", "detalle": "Ya vinculado."}
    assert body(Conflict())["codigo"] == "conflicto"


def test_http_statuses_without_a_business_code():
    assert body(exceptions.NotAuthenticated())["codigo"] == "no_autenticado"
    assert body(exceptions.Throttled())["codigo"] == "demasiadas_solicitudes"


def test_unexpected_exceptions_are_still_500():
    assert handle_exception(RuntimeError("fallo"), {}) is None


def test_first_message_tolerates_empty_details():
    assert first_message([]) == ""
    assert first_message({}) == ""
