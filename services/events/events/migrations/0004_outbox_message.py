import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    # Depende de las dos 0003 (#238 y #244, fusionadas en paralelo): además de crear la tabla
    # del outbox, une las dos ramas del grafo de migraciones.
    dependencies = [
        ("events", "0003_priority_modifier"),
        ("events", "0003_recurrence_policy"),
    ]

    operations = [
        migrations.CreateModel(
            name="OutboxMessage",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("aggregate_id", models.UUIDField()),
                ("message_type", models.CharField(max_length=80)),
                ("version", models.PositiveSmallIntegerField(default=1)),
                ("subject", models.CharField(max_length=120)),
                ("payload", models.JSONField(default=dict)),
                ("occurred_at", models.DateTimeField()),
                ("correlation_id", models.UUIDField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("PUBLISHED", "Publicado"),
                            ("FAILED", "Fallido"),
                        ],
                        default="PENDING",
                        max_length=10,
                    ),
                ),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("next_attempt_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_error", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "outbox_message",
                "ordering": ["created_at"],
                "indexes": [
                    models.Index(
                        fields=["status", "next_attempt_at"], name="ix_outbox_status_next"
                    ),
                    models.Index(fields=["aggregate_id", "created_at"], name="ix_outbox_aggregate"),
                ],
            },
        ),
    ]
