"""POST /api/problems/v1/problemas/{id}/estado/: transiciones, causa raíz y resuelto_en (#271)."""

from itertools import product

import pytest

from problems import states
from problems.models import Problem
from tests.factories import ProblemFactory

pytestmark = pytest.mark.django_db

S = Problem.Status

# Especificación de #271, separada de problems.states para no probar la tabla contra sí misma.
ALLOWED = {
    (S.REGISTERED, S.IN_ANALYSIS),
    (S.REGISTERED, S.CLOSED),
    (S.IN_ANALYSIS, S.ROOT_CAUSE_IDENTIFIED),
    (S.IN_ANALYSIS, S.REGISTERED),
    (S.ROOT_CAUSE_IDENTIFIED, S.KNOWN_ERROR),
    (S.ROOT_CAUSE_IDENTIFIED, S.RESOLVED),
    (S.ROOT_CAUSE_IDENTIFIED, S.IN_ANALYSIS),
    (S.KNOWN_ERROR, S.RESOLVED),
    (S.KNOWN_ERROR, S.IN_ANALYSIS),
    (S.RESOLVED, S.CLOSED),
    (S.RESOLVED, S.IN_ANALYSIS),
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
    assert states.ROOT_CAUSE_REQUIRED_STATES == {S.ROOT_CAUSE_IDENTIFIED, S.KNOWN_ERROR}


@pytest.mark.parametrize(("current", "target"), sorted(ALLOWED))
def test_allowed_transitions(api, current, target):
    problem = ProblemFactory(status=current, root_cause="Causa previa.")
    response = api.post(state_url(problem), {"estado": target}, format="json")
    assert response.status_code == 200
    assert response.json()["estado"] == target
    problem.refresh_from_db()
    assert problem.status == target
    assert problem.root_cause == "Causa previa."


@pytest.mark.parametrize(("current", "target"), FORBIDDEN)
def test_forbidden_transitions_are_409(api, current, target):
    problem = ProblemFactory(status=current, root_cause="Causa previa.")
    response = api.post(state_url(problem), {"estado": target}, format="json")
    assert response.status_code == 409
    assert response.json() == {
        "codigo": "transicion_invalida",
        "detalle": f"No se puede pasar de {current} a {target}.",
    }
    problem.refresh_from_db()
    assert problem.status == current


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.CLOSED, S.IN_ANALYSIS),
        (S.REGISTERED, S.RESOLVED),
        (S.IN_ANALYSIS, S.IN_ANALYSIS),
        (S.KNOWN_ERROR, S.ROOT_CAUSE_IDENTIFIED),
    ],
)
def test_forbidden_transition_examples(api, current, target):
    problem = ProblemFactory(status=current)
    assert api.post(state_url(problem), {"estado": target}, format="json").status_code == 409


def test_invalid_transition_is_checked_before_root_cause(api):
    problem = ProblemFactory(status=S.REGISTERED)
    response = api.post(state_url(problem), {"estado": S.ROOT_CAUSE_IDENTIFIED}, format="json")
    assert response.status_code == 409


# --- Root cause ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("current", "target"),
    [(S.IN_ANALYSIS, S.ROOT_CAUSE_IDENTIFIED), (S.ROOT_CAUSE_IDENTIFIED, S.KNOWN_ERROR)],
)
@pytest.mark.parametrize("sent", [None, "", "   "])
def test_missing_root_cause_is_400(api, current, target, sent):
    problem = ProblemFactory(status=current, root_cause="")
    payload = {"estado": target} if sent is None else {"estado": target, "causa_raiz": sent}
    response = api.post(state_url(problem), payload, format="json")
    assert response.status_code == 400
    assert response.json() == {
        "codigo": "datos_invalidos",
        "detalle": "La solicitud tiene campos inválidos.",
        "campos": {"causa_raiz": f"Se requiere la causa raíz para pasar a {target}."},
    }
    problem.refresh_from_db()
    assert problem.status == current


def test_root_cause_from_body_is_saved_with_the_change(api):
    problem = ProblemFactory(status=S.IN_ANALYSIS, root_cause="")
    payload = {"estado": S.ROOT_CAUSE_IDENTIFIED, "causa_raiz": "Certificado TLS vencido."}
    body = api.post(state_url(problem), payload, format="json").json()
    assert body["causa_raiz"] == "Certificado TLS vencido."
    problem.refresh_from_db()
    assert (problem.status, problem.root_cause) == (
        S.ROOT_CAUSE_IDENTIFIED,
        "Certificado TLS vencido.",
    )


def test_stored_root_cause_is_enough(api):
    problem = ProblemFactory(status=S.IN_ANALYSIS, root_cause="Guardada antes.")
    body = api.post(state_url(problem), {"estado": S.ROOT_CAUSE_IDENTIFIED}, format="json").json()
    assert body["estado"] == S.ROOT_CAUSE_IDENTIFIED
    assert body["causa_raiz"] == "Guardada antes."


def test_root_cause_from_body_replaces_the_stored_one(api):
    problem = ProblemFactory(status=S.ROOT_CAUSE_IDENTIFIED, root_cause="Hipótesis inicial.")
    payload = {"estado": S.KNOWN_ERROR, "causa_raiz": "Causa confirmada."}
    body = api.post(state_url(problem), payload, format="json").json()
    assert body["causa_raiz"] == "Causa confirmada."


def test_empty_root_cause_in_body_does_not_fall_back_to_the_stored_one(api):
    problem = ProblemFactory(status=S.IN_ANALYSIS, root_cause="Guardada antes.")
    payload = {"estado": S.ROOT_CAUSE_IDENTIFIED, "causa_raiz": ""}
    assert api.post(state_url(problem), payload, format="json").status_code == 400
    problem.refresh_from_db()
    assert problem.root_cause == "Guardada antes."


def test_root_cause_is_saved_for_states_that_do_not_require_it(api):
    problem = ProblemFactory(status=S.REGISTERED)
    payload = {"estado": S.IN_ANALYSIS, "causa_raiz": "Primera hipótesis."}
    body = api.post(state_url(problem), payload, format="json").json()
    assert body["causa_raiz"] == "Primera hipótesis."


# --- resolved_at (resuelto_en en el JSON) ------------------------------------------------------


@pytest.mark.parametrize("current", [S.ROOT_CAUSE_IDENTIFIED, S.KNOWN_ERROR])
def test_resolving_sets_resolved_at(api, current):
    problem = ProblemFactory(status=current)
    assert problem.resolved_at is None
    body = api.post(state_url(problem), {"estado": S.RESOLVED}, format="json").json()
    assert body["resuelto_en"] is not None
    problem.refresh_from_db()
    assert problem.resolved_at is not None


def test_reopening_clears_resolved_at(api):
    problem = ProblemFactory(status=S.RESOLVED)
    assert problem.resolved_at is not None
    body = api.post(state_url(problem), {"estado": S.IN_ANALYSIS}, format="json").json()
    assert body["estado"] == S.IN_ANALYSIS
    assert body["resuelto_en"] is None
    problem.refresh_from_db()
    assert problem.resolved_at is None


def test_closing_a_resolved_problem_keeps_resolved_at(api):
    problem = ProblemFactory(status=S.RESOLVED)
    before = problem.resolved_at
    api.post(state_url(problem), {"estado": S.CLOSED}, format="json")
    problem.refresh_from_db()
    assert problem.resolved_at == before


def test_closing_without_resolving_keeps_resolved_at_null(api):
    problem = ProblemFactory(status=S.REGISTERED)
    body = api.post(state_url(problem), {"estado": S.CLOSED}, format="json").json()
    assert body["resuelto_en"] is None


def test_state_change_updates_updated_at(api):
    problem = ProblemFactory(status=S.REGISTERED)
    before = problem.updated_at
    api.post(state_url(problem), {"estado": S.IN_ANALYSIS}, format="json")
    problem.refresh_from_db()
    assert problem.updated_at > before


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
