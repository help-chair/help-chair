import secrets
from concurrent.futures import ThreadPoolExecutor
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection, connections

from problems.management.commands.seed_demo import DEMO_ID, ROWS
from problems.models import KnownError, Problem, ProblemIncident

pytestmark = pytest.mark.django_db(transaction=True)


def seed():
    call_command("seed_demo", confirm_demo=True, stdout=StringIO())


def counts():
    return tuple(model.objects.count() for model, _ in ROWS)


def sequence_value(model, value):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence(%s, %s), %s, true)",
            [model._meta.db_table, model._meta.pk.column, value],
        )


def test_seed_requires_opt_in_and_does_not_write():
    before = counts()
    with pytest.raises(CommandError, match="requiere --confirm-demo"):
        call_command("seed_demo", stdout=StringIO())
    assert counts() == before


def test_seed_is_repeatable_preserves_existing_rows_and_dates():
    unrelated = Problem.objects.create(
        title="Registro ajeno", description="Conservar este registro."
    )
    seed()
    problem = Problem.objects.get(pk=DEMO_ID)
    created = problem.created_at
    updated = problem.updated_at
    seed()
    assert counts() == (2, 1, 1)
    problem.refresh_from_db()
    unrelated.refresh_from_db()
    assert unrelated.title == "Registro ajeno"
    assert problem.created_at == created
    assert problem.updated_at == updated
    error = KnownError.objects.get(pk=DEMO_ID)
    link = ProblemIncident.objects.get(pk=DEMO_ID)
    assert link.problem_id == error.problem_id == problem.pk
    assert error.root_cause == problem.root_cause
    assert error.workaround
    assert error.kb_article_id == ""


def test_collision_does_not_overwrite_an_unrelated_problem():
    occupied = Problem.objects.create(pk=DEMO_ID, title="Ajeno", description="No reemplazar.")
    with pytest.raises(CommandError, match="ID reservado"):
        seed()
    occupied.refresh_from_db()
    assert occupied.title == "Ajeno"
    assert counts() == (1, 0, 0)


def test_later_collision_leaves_no_partial_demo_rows():
    owner = Problem.objects.create(title="Ajeno", description="Registro previo.")
    KnownError.objects.create(
        pk=DEMO_ID,
        problem=owner,
        title="Ajeno",
        description="No reemplazar.",
        root_cause="Causa del registro ajeno.",
        workaround="Solución temporal ajena.",
    )
    with pytest.raises(CommandError, match="ID reservado"):
        seed()
    assert counts() == (1, 0, 1)
    assert not Problem.objects.filter(pk=DEMO_ID).exists()


def test_database_failure_rolls_back_rows_and_does_not_disclose_details(monkeypatch):
    private_value = secrets.token_urlsafe(40)

    def fail(**kwargs):
        raise IntegrityError(private_value)

    monkeypatch.setattr(KnownError.objects, "create", fail)
    with pytest.raises(CommandError, match="no se completó la operación") as caught:
        seed()
    safe_error = private_value not in str(caught.value) and caught.value.__suppress_context__
    assert safe_error, "Seed errors must not expose database exception details"
    assert counts() == (0, 0, 0)


def test_concurrent_seed_calls_keep_one_demo_set():
    def load_demo():
        try:
            seed()
            return True
        except CommandError:
            return False
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(load_demo) for _ in range(2)]
        completed = all(future.result(timeout=15) for future in futures)
    assert completed, "Concurrent demo loads must complete without partial data"
    assert counts() == (1, 1, 1)


def test_edited_demo_is_preserved_and_requires_operator_resolution():
    seed()
    Problem.objects.filter(pk=DEMO_ID).update(title="Ejemplo editado")
    with pytest.raises(CommandError, match="ejemplo fue modificado"):
        seed()
    assert Problem.objects.get(pk=DEMO_ID).title == "Ejemplo editado"
    assert counts() == (1, 1, 1)


def test_sequences_allow_subsequent_automatic_ids_for_all_three_models():
    seed()
    problem = Problem.objects.create(title="Alta posterior", description="ID automático.")
    error = KnownError.objects.create(
        problem=problem,
        title="Error posterior",
        description="ID automático.",
        root_cause="Causa de ensayo.",
        workaround="Solución temporal de ensayo.",
    )
    link = ProblemIncident.objects.create(problem=problem, incident_id="INC-POSTERIOR")
    assert all(row.pk > DEMO_ID for row in (problem, error, link))


def test_seed_never_rewinds_sequences_already_ahead():
    ahead = DEMO_ID + 1000
    for model, _ in ROWS:
        sequence_value(model, ahead)
    seed()
    problem = Problem.objects.create(title="Alta posterior", description="Secuencia adelantada.")
    error = KnownError.objects.create(
        problem=problem,
        title="Error posterior",
        description="Secuencia adelantada.",
        root_cause="Causa de ensayo.",
        workaround="Solución temporal de ensayo.",
    )
    link = ProblemIncident.objects.create(problem=problem, incident_id="INC-ADELANTADO")
    assert all(row.pk > ahead for row in (problem, error, link))
