"""Siembra la configuración de prioridad por defecto: matriz impacto × urgencia y modificadores.

Se ejecuta con ``make seed``. Es idempotente y no pisa lo que la empresa ya configuró: solo crea
las filas que faltan. Con ``--reset`` restablece los valores por defecto.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from events.models import (
    Impact,
    ModifierField,
    Priority,
    PriorityMatrix,
    PriorityModifier,
    ServiceImportance,
    Urgency,
)

DEFAULT_MATRIX: dict[tuple[str, str], str] = {
    (Impact.HIGH, Urgency.HIGH): Priority.CRITICAL,
    (Impact.HIGH, Urgency.MEDIUM): Priority.HIGH,
    (Impact.HIGH, Urgency.LOW): Priority.MEDIUM,
    (Impact.MEDIUM, Urgency.HIGH): Priority.HIGH,
    (Impact.MEDIUM, Urgency.MEDIUM): Priority.MEDIUM,
    (Impact.MEDIUM, Urgency.LOW): Priority.LOW,
    (Impact.LOW, Urgency.HIGH): Priority.MEDIUM,
    (Impact.LOW, Urgency.MEDIUM): Priority.LOW,
    (Impact.LOW, Urgency.LOW): Priority.LOW,
}

DEFAULT_MODIFIERS: tuple[dict, ...] = (
    {
        "code": "servicio-critico",
        "condition_field": ModifierField.SERVICE_IMPORTANCE,
        "condition_value": ServiceImportance.CRITICAL,
        "levels_delta": 1,
    },
    {
        "code": "servicio-baja-importancia",
        "condition_field": ModifierField.SERVICE_IMPORTANCE,
        "condition_value": ServiceImportance.LOW,
        "levels_delta": -1,
    },
    {
        "code": "recurrencia-10",
        "condition_field": ModifierField.OCCURRENCE_COUNT,
        "condition_value": "10",
        "levels_delta": 1,
    },
)


class Command(BaseCommand):
    help = "Siembra la matriz de prioridad y los modificadores por defecto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Restablece los valores por defecto aunque ya existan.",
        )

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        matrix_created = 0
        for (impact, urgency), priority in DEFAULT_MATRIX.items():
            if reset:
                _, created = PriorityMatrix.objects.update_or_create(
                    impact=impact,
                    urgency=urgency,
                    defaults={"priority": priority, "updated_by_ref": "system"},
                )
            else:
                _, created = PriorityMatrix.objects.get_or_create(
                    impact=impact,
                    urgency=urgency,
                    defaults={"priority": priority, "created_by_ref": "system"},
                )
            matrix_created += created

        modifiers_created = 0
        for data in DEFAULT_MODIFIERS:
            values = {key: value for key, value in data.items() if key != "code"}
            if reset:
                _, created = PriorityModifier.objects.update_or_create(
                    code=data["code"],
                    defaults={**values, "is_active": True, "updated_by_ref": "system"},
                )
            else:
                _, created = PriorityModifier.objects.get_or_create(
                    code=data["code"],
                    defaults={**values, "created_by_ref": "system"},
                )
            modifiers_created += created

        self.stdout.write(
            self.style.SUCCESS(
                f"Matriz: {matrix_created} celdas nuevas de {len(DEFAULT_MATRIX)}. "
                f"Modificadores: {modifiers_created} nuevos de {len(DEFAULT_MODIFIERS)}."
            )
        )
