"""Renombra modelos y campos a inglés sin tocar los datos.

Solo usa operaciones de renombre (ALTER TABLE ... RENAME): ninguna tabla ni columna se borra y
vuelve a crear. La UniqueConstraint se quita antes de renombrar ``problema`` porque Django no
actualiza los campos de una constraint al renombrarlos, y se vuelve a crear con nombre en inglés
al final, dentro de la misma transacción.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("problems", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="problemaincidente",
            name="problema_incidente_unico",
        ),
        # Modelos (y sus tablas): problems_problema -> problems_problem, etc.
        migrations.RenameModel(old_name="Problema", new_name="Problem"),
        migrations.RenameModel(old_name="ProblemaIncidente", new_name="ProblemIncident"),
        migrations.RenameModel(old_name="ErrorConocido", new_name="KnownError"),
        # Problem
        migrations.RenameField(model_name="problem", old_name="titulo", new_name="title"),
        migrations.RenameField(
            model_name="problem", old_name="descripcion", new_name="description"
        ),
        migrations.RenameField(model_name="problem", old_name="estado", new_name="status"),
        migrations.RenameField(model_name="problem", old_name="prioridad", new_name="priority"),
        migrations.RenameField(model_name="problem", old_name="origen", new_name="origin"),
        migrations.RenameField(model_name="problem", old_name="causa_raiz", new_name="root_cause"),
        migrations.RenameField(
            model_name="problem", old_name="asignado_a_id", new_name="assignee_id"
        ),
        migrations.RenameField(model_name="problem", old_name="creado_en", new_name="created_at"),
        migrations.RenameField(
            model_name="problem", old_name="actualizado_en", new_name="updated_at"
        ),
        migrations.RenameField(
            model_name="problem", old_name="resuelto_en", new_name="resolved_at"
        ),
        # ProblemIncident
        migrations.RenameField(
            model_name="problemincident", old_name="problema", new_name="problem"
        ),
        migrations.RenameField(
            model_name="problemincident", old_name="incidente_id", new_name="incident_id"
        ),
        migrations.RenameField(
            model_name="problemincident", old_name="vinculado_en", new_name="linked_at"
        ),
        # KnownError
        migrations.RenameField(model_name="knownerror", old_name="problema", new_name="problem"),
        migrations.RenameField(model_name="knownerror", old_name="titulo", new_name="title"),
        migrations.RenameField(
            model_name="knownerror", old_name="descripcion", new_name="description"
        ),
        migrations.RenameField(
            model_name="knownerror", old_name="causa_raiz", new_name="root_cause"
        ),
        migrations.RenameField(
            model_name="knownerror", old_name="articulo_kb_id", new_name="kb_article_id"
        ),
        migrations.RenameField(model_name="knownerror", old_name="activo", new_name="is_active"),
        migrations.RenameField(
            model_name="knownerror", old_name="creado_en", new_name="created_at"
        ),
        migrations.RenameField(
            model_name="knownerror", old_name="actualizado_en", new_name="updated_at"
        ),
        # related_name y ordering solo existen en el estado de Django: no tocan la base.
        migrations.AlterField(
            model_name="problemincident",
            name="problem",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="incidents",
                to="problems.problem",
                verbose_name="problema",
            ),
        ),
        migrations.AlterField(
            model_name="knownerror",
            name="problem",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="known_errors",
                to="problems.problem",
                verbose_name="problema",
            ),
        ),
        migrations.AlterModelOptions(
            name="problem",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "problema",
                "verbose_name_plural": "problemas",
            },
        ),
        migrations.AlterModelOptions(
            name="knownerror",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "error conocido",
                "verbose_name_plural": "errores conocidos",
            },
        ),
        migrations.AddConstraint(
            model_name="problemincident",
            constraint=models.UniqueConstraint(
                fields=("problem", "incident_id"), name="problem_incident_unique"
            ),
        ),
    ]
