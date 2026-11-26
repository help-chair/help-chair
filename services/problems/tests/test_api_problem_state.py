"""POST /api/problems/v1/problemas/{id}/estado/: transiciones, causa raíz y resuelto_en (#271)."""

from itertools import product

import pytest

from problems import states
from problems.models import Problema
from tests.factories import ProblemFactory

pytestmark = pytest.mark.django_db

S = Problema.Estado

# Especificación de #271, separada de problems.states para no probar la tabla contra sí misma.
ALLOWED = {
    (S.REGISTRADO, S.EN_ANALISIS),
    (S.REGISTRADO, S.CERRADO),
    (S.EN_ANALISIS, S.CAUSA_IDENTIFICADA),
    (S.EN_ANALISIS, S.REGISTRADO),
    (S.CAUSA_IDENTIFICADA, S.ERROR_CONOCIDO),
    (S.CAUSA_IDENTIFICADA, S.RESUELTO),
    (S.CAUSA_IDENTIFICADA, S.EN_ANALISIS),
    (S.ERROR_CONOCIDO, S.RESUELTO),
    (S.ERROR_CONOCIDO, S.EN_ANALISIS),
    (S.RESUELTO, S.CERRADO),
    (S.RESUELTO, S.EN_ANALISIS),
}
FORBIDDEN = sorted(set(product(S.values, S.values)) - ALLOWED)


def state_url(problem):
    return f"/api/problems/v1/problemas/{problem.pk}/estado/"


def test_central_transition_table_matches_the_specification():
    table = {
        (current, target)
        for current, targets in states.ALLOWED_TRANSITIONS.items()
        for target in targets
    }
    assert table == ALLOWED
    assert set(states.ALLOWED_TRANSITIONS) == set(S.values)
    assert states.ROOT_CAUSE_REQUIRED_STATES == {S.CAUSA_IDENTIFICADA, S.ERROR_CONOCIDO}


@pytest.mark.parametrize(("current", "target"), sorted(ALLOWED))
def test_allowed_transitions(api, current, target):
    problem = ProblemFactory(estado=current, causa_raiz="Causa previa.")
    response = api.post(state_url(problem), {"estado": target}, format="json")
    assert response.status_code == 200
    assert response.json()["estado"] == target
    problem.refresh_from_db()
    assert problem.estado == target
    assert problem.causa_raiz == "Causa previa."


@pytest.mark.parametrize(("current", "target"), FORBIDDEN)
def test_forbidden_transitions_are_409(api, current, target):
    problem = ProblemFactory(estado=current, causa_raiz="Causa previa.")
    response = api.post(state_url(problem), {"estado": target}, format="json")
    assert response.status_code == 409
    assert response.json() == {
        "codigo": "transicion_invalida",
        "detalle": f"No se puede pasar de {current} a {target}.",
    }
    problem.refresh_from_db()
    assert problem.estado == current


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.CERRADO, S.EN_ANALISIS),
        (S.REGISTRADO, S.RESUELTO),
        (S.EN_ANALISIS, S.EN_ANALISIS),
        (S.ERROR_CONOCIDO, S.CAUSA_IDENTIFICADA),
    ],
)
def test_forbidden_transition_examples(api, current, target):
    problem = ProblemFactory(estado=current)
    assert api.post(state_url(problem), {"estado": target}, format="json").status_code == 409


def test_invalid_transition_is_checked_before_root_cause(api):
    problem = ProblemFactory(estado=S.REGISTRADO)
    response = api.post(state_url(problem), {"estado": S.CAUSA_IDENTIFICADA}, format="json")
    assert response.status_code == 409


# --- Root cause ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("current", "target"),
    [(S.EN_ANALISIS, S.CAUSA_IDENTIFICADA), (S.CAUSA_IDENTIFICADA, S.ERROR_CONOCIDO)],
)
@pytest.mark.parametrize("sent", [None, "", "   "])
def test_missing_root_cause_is_400(api, current, target, sent):
    problem = ProblemFactory(estado=current, causa_raiz="")
    payload = {"estado": target} if sent is None else {"estado": target, "causa_raiz": sent}
    response = api.post(state_url(problem), payload, format="json")
    assert response.status_code == 400
    assert response.json() == {
        "codigo": "datos_invalidos",
        "detalle": "La solicitud tiene campos inválidos.",
        "campos": {"causa_raiz": f"Se requiere la causa raíz para pasar a {target}."},
    }
    problem.refresh_from_db()
    assert problem.estado == current


def test_root_cause_from_body_is_saved_with_the_change(api):
    problem = ProblemFactory(estado=S.EN_ANALISIS, causa_raiz="")
    payload = {"estado": S.CAUSA_IDENTIFICADA, "causa_raiz": "Certificado TLS vencido."}
    body = api.post(state_url(problem), payload, format="json").json()
    assert body["causa_raiz"] == "Certificado TLS vencido."
    problem.refresh_from_db()
    assert (problem.estado, problem.causa_raiz) == (
        S.CAUSA_IDENTIFICADA,
        "Certificado TLS vencido.",
    )


def test_stored_root_cause_is_enough(api):
    problem = ProblemFactory(estado=S.EN_ANALISIS, causa_raiz="Guardada antes.")
    body = api.post(state_url(problem), {"estado": S.CAUSA_IDENTIFICADA}, format="json").json()
    assert body["estado"] == S.CAUSA_IDENTIFICADA
    assert body["causa_raiz"] == "Guardada antes."


def test_root_cause_from_body_replaces_the_stored_one(api):
    problem = ProblemFactory(estado=S.CAUSA_IDENTIFICADA, causa_raiz="Hipótesis inicial.")
    payload = {"estado": S.ERROR_CONOCIDO, "causa_raiz": "Causa confirmada."}
    body = api.post(state_url(problem), payload, format="json").json()
    assert body["causa_raiz"] == "Causa confirmada."


def test_empty_root_cause_in_body_does_not_fall_back_to_the_stored_one(api):
    problem = ProblemFactory(estado=S.EN_ANALISIS, causa_raiz="Guardada antes.")
    payload = {"estado": S.CAUSA_IDENTIFICADA, "causa_raiz": ""}
    assert api.post(state_url(problem), payload, format="json").status_code == 400
    problem.refresh_from_db()
    assert problem.causa_raiz == "Guardada antes."


def test_root_cause_is_saved_for_states_that_do_not_require_it(api):
    problem = ProblemFactory(estado=S.REGISTRADO)
    payload = {"estado": S.EN_ANALISIS, "causa_raiz": "Primera hipótesis."}
    body = api.post(state_url(problem), payload, format="json").json()
    assert body["causa_raiz"] == "Primera hipótesis."


# --- resuelto_en ---------------------------------------------------------------------------------


@pytest.mark.parametrize("current", [S.CAUSA_IDENTIFICADA, S.ERROR_CONOCIDO])
def test_resolving_sets_resuelto_en(api, current):
    problem = ProblemFactory(estado=current)
    assert problem.resuelto_en is None
    body = api.post(state_url(problem), {"estado": S.RESUELTO}, format="json").json()
    assert body["resuelto_en"] is not None
    problem.refresh_from_db()
    assert problem.resuelto_en is not None


def test_reopening_clears_resuelto_en(api):
    problem = ProblemFactory(estado=S.RESUELTO)
    assert problem.resuelto_en is not None
    body = api.post(state_url(problem), {"estado": S.EN_ANALISIS}, format="json").json()
    assert body["estado"] == S.EN_ANALISIS
    assert body["resuelto_en"] is None
    problem.refresh_from_db()
    assert problem.resuelto_en is None


def test_closing_a_resolved_problem_keeps_resuelto_en(api):
    problem = ProblemFactory(estado=S.RESUELTO)
    before = problem.resuelto_en
    api.post(state_url(problem), {"estado": S.CERRADO}, format="json")
    problem.refresh_from_db()
    assert problem.resuelto_en == before


def test_closing_without_resolving_keeps_resuelto_en_null(api):
    problem = ProblemFactory(estado=S.REGISTRADO)
    body = api.post(state_url(problem), {"estado": S.CERRADO}, format="json").json()
    assert body["resuelto_en"] is None


def test_state_change_updates_actualizado_en(api):
    problem = ProblemFactory(estado=S.REGISTRADO)
    before = problem.actualizado_en
    api.post(state_url(problem), {"estado": S.EN_ANALISIS}, format="json")
    problem.refresh_from_db()
    assert problem.actualizado_en > before


# --- Request errors ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload", [{}, {"estado": "abierto"}, {"estado": None}, {"causa_raiz": "Sin estado."}]
)
def test_invalid_body_is_400(api, payload):
    problem = ProblemFactory()
    response = api.post(state_url(problem), payload, format="json")
    assert response.status_code == 400
    body = response.json()
    assert body["codigo"] == "datos_invalidos"
    assert set(body["campos"]) == {"estado"}
    assert isinstance(body["campos"]["estado"], str)


def test_missing_problem_is_404(api):
    response = api.post("/api/problems/v1/problemas/999999/estado/", {"estado": "en_analisis"})
    assert response.status_code == 404
    assert response.json()["codigo"] == "no_encontrado"
