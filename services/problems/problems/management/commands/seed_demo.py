"""Datos sintéticos de Problems, exclusivamente para una BD de demostración."""

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection, transaction

from problems.models import ErrorConocido, Problema, ProblemaIncidente

DEMO_ID = 1100001
LOCK_ID = 11020261122
CAUSE = "La renovación programada del certificado del servidor de ensayo está desactivada."
ROWS = (
    (
        Problema,
        {
            "titulo": "Demo Problems: interrupciones del correo de ensayo",
            "descripcion": "Incidentes sintéticos de conexión TLS al correo de demostración.",
            "estado": Problema.Estado.ERROR_CONOCIDO,
            "prioridad": Problema.Prioridad.MEDIA,
            "origen": Problema.Origen.MANUAL,
            "causa_raiz": CAUSE,
            "asignado_a_id": "",
            "resuelto_en": None,
        },
    ),
    (
        ProblemaIncidente,
        {"problema_id": DEMO_ID, "incidente_id": "DEMO-PROBLEMS-110-INCIDENTE"},
    ),
    (
        ErrorConocido,
        {
            "problema_id": DEMO_ID,
            "titulo": "Demo Problems: certificado de correo vencido",
            "descripcion": "El servidor de ensayo rechaza conexiones TLS.",
            "causa_raiz": CAUSE,
            "workaround": "Renovar manualmente el certificado del entorno de ensayo.",
            "articulo_kb_id": "",
            "activo": True,
        },
    ),
)


def advance_sequence(cursor, model):
    """Avanza hasta MAX(pk) sin rebobinar una secuencia ya adelantada."""
    table = model._meta.db_table
    column = model._meta.pk.column
    quote = connection.ops.quote_name
    cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, column])
    sequence = cursor.fetchone()[0]
    if not sequence:
        raise CommandError("Seed cancelado: falta una secuencia del esquema existente.")
    cursor.execute(
        "SELECT n.nspname, c.relname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.oid = %s::regclass",
        [sequence],
    )
    schema, name = cursor.fetchone()
    qualified = f"{quote(schema)}.{quote(name)}"
    cursor.execute(f"SELECT last_value, is_called FROM {qualified}")
    last_value, is_called = cursor.fetchone()
    cursor.execute(f"SELECT MAX({quote(column)}) FROM {quote(table)}")
    maximum = cursor.fetchone()[0]
    if maximum is not None and (maximum > last_value or (maximum == last_value and not is_called)):
        cursor.execute("SELECT setval(%s::regclass, %s, true)", [sequence, maximum])


class Command(BaseCommand):
    help = "Carga ejemplos propios de Problems sin sobrescribir registros; solo para BD de ensayo."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-demo", action="store_true")

    def handle(self, *args, **options):
        if not options["confirm_demo"]:
            raise CommandError("Seed desactivado: requiere --confirm-demo y una BD de ensayo.")
        if connection.vendor != "postgresql":
            raise CommandError("Seed cancelado: requiere PostgreSQL explícito.")
        try:
            self.seed()
        except DatabaseError:
            raise CommandError(
                "Seed cancelado: no se completó la operación de base de datos."
            ) from None
        self.stdout.write("Demo Problems disponible: un problema, un vínculo y un error conocido.")

    @transaction.atomic
    def seed(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [LOCK_ID])
            # Excluye INSERT/UPDATE/DELETE mientras se comprueban IDs y secuencias.
            # No es un mecanismo para usar el seed con tráfico de producción.
            tables = ", ".join(connection.ops.quote_name(model._meta.db_table) for model, _ in ROWS)
            cursor.execute(f"LOCK TABLE {tables} IN SHARE ROW EXCLUSIVE MODE")
            missing = []
            for model, values in ROWS:
                row = model.objects.filter(pk=DEMO_ID).first()
                if row is None:
                    missing.append((model, values))
                elif any(getattr(row, field) != value for field, value in values.items()):
                    raise CommandError(
                        "Seed cancelado: un ID reservado está ocupado o el ejemplo fue modificado."
                    )
            for model, values in missing:
                model.objects.create(pk=DEMO_ID, **values)
            for model, _ in ROWS:
                advance_sequence(cursor, model)
