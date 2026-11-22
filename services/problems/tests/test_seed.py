import secrets
from concurrent.futures import ThreadPoolExecutor
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection, connections

from problems.management.commands.seed_demo import DEMO_ID, ROWS
from problems.models import ErrorConocido, Problema, ProblemaIncidente

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
    unrelated = Problema.objects.create(
        titulo="Registro ajeno", descripcion="Conservar este registro."
    )
    seed()
    problem = Problema.objects.get(pk=DEMO_ID)
    created = problem.creado_en
    updated = problem.actualizado_en
    seed()
    assert counts() == (2, 1, 1)
    problem.refresh_from_db()
    unrelated.refresh_from_db()
    assert unrelated.titulo == "Registro ajeno"
    assert problem.creado_en == created
    assert problem.actualizado_en == updated
    error = ErrorConocido.objects.get(pk=DEMO_ID)
    link = ProblemaIncidente.objects.get(pk=DEMO_ID)
    assert link.problema_id == error.problema_id == problem.pk
    assert error.causa_raiz == problem.causa_raiz
    assert error.workaround
    assert error.articulo_kb_id == ""


def test_collision_does_not_overwrite_an_unrelated_problem():
    occupied = Problema.objects.create(pk=DEMO_ID, titulo="Ajeno", descripcion="No reemplazar.")
    with pytest.raises(CommandError, match="ID reservado"):
        seed()
    occupied.refresh_from_db()
    assert occupied.titulo == "Ajeno"
    assert counts() == (1, 0, 0)


def test_later_collision_leaves_no_partial_demo_rows():
    owner = Problema.objects.create(titulo="Ajeno", descripcion="Registro previo.")
    ErrorConocido.objects.create(
        pk=DEMO_ID,
        problema=owner,
        titulo="Ajeno",
        descripcion="No reemplazar.",
        causa_raiz="Causa del registro ajeno.",
        workaround="Solución temporal ajena.",
    )
    with pytest.raises(CommandError, match="ID reservado"):
        seed()
    assert counts() == (1, 0, 1)
    assert not Problema.objects.filter(pk=DEMO_ID).exists()


def test_database_failure_rolls_back_rows_and_does_not_disclose_details(monkeypatch):
    private_value = secrets.token_urlsafe(40)

    def fail(**kwargs):
        raise IntegrityError(private_value)

    monkeypatch.setattr(ErrorConocido.objects, "create", fail)
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
    Problema.objects.filter(pk=DEMO_ID).update(titulo="Ejemplo editado")
    with pytest.raises(CommandError, match="ejemplo fue modificado"):
        seed()
    assert Problema.objects.get(pk=DEMO_ID).titulo == "Ejemplo editado"
    assert counts() == (1, 1, 1)


def test_sequences_allow_subsequent_automatic_ids_for_all_three_models():
    seed()
    problem = Problema.objects.create(titulo="Alta posterior", descripcion="ID automático.")
    error = ErrorConocido.objects.create(
        problema=problem,
        titulo="Error posterior",
        descripcion="ID automático.",
        causa_raiz="Causa de ensayo.",
        workaround="Solución temporal de ensayo.",
    )
    link = ProblemaIncidente.objects.create(problema=problem, incidente_id="INC-POSTERIOR")
    assert all(row.pk > DEMO_ID for row in (problem, error, link))


def test_seed_never_rewinds_sequences_already_ahead():
    ahead = DEMO_ID + 1000
    for model, _ in ROWS:
        sequence_value(model, ahead)
    seed()
    problem = Problema.objects.create(titulo="Alta posterior", descripcion="Secuencia adelantada.")
    error = ErrorConocido.objects.create(
        problema=problem,
        titulo="Error posterior",
        descripcion="Secuencia adelantada.",
        causa_raiz="Causa de ensayo.",
        workaround="Solución temporal de ensayo.",
    )
    link = ProblemaIncidente.objects.create(problema=problem, incidente_id="INC-ADELANTADO")
    assert all(row.pk > ahead for row in (problem, error, link))
