import pytest
from django.db import IntegrityError, transaction

from problems.models import KnownError, Problem, ProblemIncident

pytestmark = pytest.mark.django_db


def create_problem(**kwargs):
    data = {"title": "Caída del correo", "description": "El correo falla cada lunes."}
    data.update(kwargs)
    return Problem.objects.create(**data)


def test_problem_defaults():
    problem = create_problem()

    assert problem.status == Problem.Status.REGISTERED
    assert problem.priority == Problem.Priority.MEDIUM
    assert problem.origin == Problem.Origin.MANUAL
    assert problem.root_cause == ""
    assert problem.assignee_id == ""
    assert problem.resolved_at is None
    assert problem.created_at is not None
    assert str(problem) == f"PRB-{problem.pk}: Caída del correo"


def test_known_error_with_workaround():
    problem = create_problem(status=Problem.Status.KNOWN_ERROR)
    error = KnownError.objects.create(
        problem=problem,
        title="Certificado SMTP vencido",
        description="El servidor SMTP rechaza conexiones.",
        root_cause="El certificado TLS no se renueva automáticamente.",
        workaround="Reiniciar el servicio de correo tras renovar el certificado a mano.",
    )

    assert error.is_active is True
    assert error.kb_article_id == ""
    assert error.workaround.startswith("Reiniciar")
    assert list(problem.known_errors.all()) == [error]
    assert str(error) == f"KE-{error.pk}: Certificado SMTP vencido"


def test_the_same_incident_cannot_be_linked_twice():
    problem = create_problem()
    ProblemIncident.objects.create(problem=problem, incident_id="INC-1")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProblemIncident.objects.create(problem=problem, incident_id="INC-1")

    assert problem.incidents.count() == 1


def test_the_same_incident_can_be_linked_to_another_problem():
    ProblemIncident.objects.create(problem=create_problem(), incident_id="INC-1")
    ProblemIncident.objects.create(problem=create_problem(), incident_id="INC-1")

    assert ProblemIncident.objects.filter(incident_id="INC-1").count() == 2


def test_choice_values_keep_the_contract_spelling():
    # Los identificadores están en inglés; los valores guardados son los del contrato.
    assert Problem.Status.ROOT_CAUSE_IDENTIFIED == "causa_identificada"
    assert Problem.Priority.CRITICAL == "critica"
    assert Problem.Origin.PATTERN == "patron"
