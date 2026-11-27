"""Renombra modelos, campos, CheckConstraint e índice a inglés sin tocar los datos.

En SQL solo hay renombres (``ALTER TABLE ... RENAME``, ``RENAME CONSTRAINT``,
``ALTER INDEX ... RENAME``): ninguna tabla, columna, restricción ni índice se borra y se vuelve a
crear. PostgreSQL actualiza solo las columnas renombradas dentro de cada CHECK e índice, pero
Django no actualiza las condiciones de su estado al renombrar un campo; por eso cada restricción
usa ``SeparateDatabaseAndState``: en la BD solo se renombra y en el estado se sustituye por su
versión con los campos nuevos. El resto (``verbose_name``, ``ordering``) son metadatos sin SQL.
"""

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def rename_constraint(table, old_name, new_name):
    return migrations.RunSQL(
        f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old_name}" TO "{new_name}"',
        reverse_sql=f'ALTER TABLE "{table}" RENAME CONSTRAINT "{new_name}" TO "{old_name}"',
    )


def replace_check(model_name, table, old_name, constraint):
    """Renombra la CHECK en la BD y actualiza su condición solo en el estado de Django."""
    return migrations.SeparateDatabaseAndState(
        database_operations=[rename_constraint(table, old_name, constraint.name)],
        state_operations=[
            migrations.RemoveConstraint(model_name=model_name, name=old_name),
            migrations.AddConstraint(model_name=model_name, constraint=constraint),
        ],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0001_initial"),
        # RenameModel renombra también el ContentType; al revertir, Django lo consulta con el
        # esquema de contenttypes vigente, que no tiene la columna ``name`` desde su 0002.
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        # Modelos (y sus tablas): articles_categoria -> articles_category, etc.
        migrations.RenameModel(old_name="Categoria", new_name="Category"),
        migrations.RenameModel(old_name="Articulo", new_name="Article"),
        # Category
        migrations.RenameField(model_name="category", old_name="codigo", new_name="code"),
        migrations.RenameField(model_name="category", old_name="nombre", new_name="name"),
        migrations.RenameField(model_name="category", old_name="activa", new_name="is_active"),
        migrations.RenameField(model_name="category", old_name="creado_en", new_name="created_at"),
        migrations.RenameField(
            model_name="category", old_name="actualizado_en", new_name="updated_at"
        ),
        # Article
        migrations.RenameField(model_name="article", old_name="titulo", new_name="title"),
        migrations.RenameField(model_name="article", old_name="contenido", new_name="content"),
        migrations.RenameField(model_name="article", old_name="categoria", new_name="category"),
        migrations.RenameField(model_name="article", old_name="estado", new_name="status"),
        migrations.RenameField(model_name="article", old_name="visibilidad", new_name="visibility"),
        migrations.RenameField(model_name="article", old_name="autor_id", new_name="author_id"),
        migrations.RenameField(model_name="article", old_name="creado_en", new_name="created_at"),
        migrations.RenameField(
            model_name="article", old_name="actualizado_en", new_name="updated_at"
        ),
        migrations.RenameField(
            model_name="article", old_name="publicado_en", new_name="published_at"
        ),
        migrations.RenameField(
            model_name="article", old_name="archivado_en", new_name="archived_at"
        ),
        # CheckConstraint de Category
        replace_check(
            "category",
            "articles_category",
            "kb_categoria_codigo_valido",
            models.CheckConstraint(
                condition=models.Q(("code__regex", "^[a-z][a-z0-9_]{0,49}$")),
                name="kb_category_code_valid",
                violation_error_message="El código debe usar minúsculas, números o guion bajo.",
            ),
        ),
        replace_check(
            "category",
            "articles_category",
            "kb_categoria_nombre_no_blanco",
            models.CheckConstraint(
                condition=models.Q(("name__regex", "[^\\s]")),
                name="kb_category_name_not_blank",
                violation_error_message="La categoría necesita un nombre no vacío.",
            ),
        ),
        replace_check(
            "category",
            "articles_category",
            "kb_categoria_fechas_validas",
            models.CheckConstraint(
                condition=models.Q(("updated_at__gte", models.F("created_at"))),
                name="kb_category_dates_valid",
                violation_error_message="La actualización no puede preceder a la creación.",
            ),
        ),
        # CheckConstraint de Article
        replace_check(
            "article",
            "articles_article",
            "kb_articulo_estado_valido",
            models.CheckConstraint(
                condition=models.Q(("status__in", ["borrador", "publicado", "archivado"])),
                name="kb_article_status_valid",
                violation_error_message="El estado no está permitido.",
            ),
        ),
        replace_check(
            "article",
            "articles_article",
            "kb_articulo_visibilidad_valida",
            models.CheckConstraint(
                condition=models.Q(("visibility__in", ["empresa", "soporte"])),
                name="kb_article_visibility_valid",
                violation_error_message="La visibilidad no está permitida.",
            ),
        ),
        replace_check(
            "article",
            "articles_article",
            "kb_articulo_publicacion_completa",
            models.CheckConstraint(
                condition=models.Q(
                    models.Q(("status", "publicado"), _negated=True),
                    models.Q(
                        ("content__regex", "[^\\s]"),
                        ("title__regex", "[^\\s]"),
                        ("author_id__isnull", False),
                        ("category__isnull", False),
                        ("published_at__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="kb_article_publication_complete",
                violation_error_message=(
                    "Para publicar completa título, contenido, categoría, autor y fecha."
                ),
            ),
        ),
        replace_check(
            "article",
            "articles_article",
            "kb_articulo_archivo_consistente",
            models.CheckConstraint(
                condition=models.Q(
                    models.Q(("archived_at__isnull", False), ("status", "archivado")),
                    models.Q(
                        models.Q(("status", "archivado"), _negated=True),
                        ("archived_at__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="kb_article_archive_consistent",
                violation_error_message="La fecha de archivo corresponde solo al estado archivado.",
            ),
        ),
        replace_check(
            "article",
            "articles_article",
            "kb_articulo_fechas_validas",
            models.CheckConstraint(
                condition=models.Q(
                    ("updated_at__gte", models.F("created_at")),
                    models.Q(
                        ("published_at__isnull", True),
                        ("published_at__gte", models.F("created_at")),
                        _connector="OR",
                    ),
                    models.Q(
                        ("archived_at__isnull", True),
                        ("archived_at__gte", models.F("created_at")),
                        _connector="OR",
                    ),
                    models.Q(
                        ("archived_at__isnull", True),
                        ("published_at__isnull", True),
                        ("archived_at__gte", models.F("published_at")),
                        _connector="OR",
                    ),
                ),
                name="kb_article_dates_valid",
                violation_error_message=(
                    "Revisa el orden de las fechas de creación, publicación y archivo."
                ),
            ),
        ),
        # Índice de consulta: mismo orden de columnas, solo cambia el nombre.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    'ALTER INDEX "kb_articulo_consulta_idx" RENAME TO "kb_article_query_idx"',
                    reverse_sql=(
                        'ALTER INDEX "kb_article_query_idx" RENAME TO "kb_articulo_consulta_idx"'
                    ),
                )
            ],
            state_operations=[
                migrations.RemoveIndex(model_name="article", name="kb_articulo_consulta_idx"),
                migrations.AddIndex(
                    model_name="article",
                    index=models.Index(
                        fields=["status", "visibility", "-updated_at", "id"],
                        name="kb_article_query_idx",
                    ),
                ),
            ],
        ),
        # Metadatos sin SQL: orden con los campos nuevos y etiquetas en español.
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["name", "code"],
                "verbose_name": "categoría",
                "verbose_name_plural": "categorías",
            },
        ),
        migrations.AlterModelOptions(
            name="article",
            options={
                "ordering": ["-updated_at", "id"],
                "verbose_name": "artículo",
                "verbose_name_plural": "artículos",
            },
        ),
        migrations.AlterField(
            model_name="category",
            name="code",
            field=models.CharField(
                max_length=50,
                primary_key=True,
                serialize=False,
                validators=[
                    django.core.validators.RegexValidator(
                        "\\A[a-z][a-z0-9_]{0,49}\\Z", "Usa un código en minúsculas."
                    )
                ],
                verbose_name="código",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(
                max_length=100,
                validators=[
                    django.core.validators.RegexValidator("\\S", "Escribe un nombre no vacío.")
                ],
                verbose_name="nombre",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="activa"),
        ),
        migrations.AlterField(
            model_name="category",
            name="created_at",
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False, verbose_name="creado en"
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="actualizado en"),
        ),
        migrations.AlterField(
            model_name="article",
            name="content",
            field=models.TextField(blank=True, default="", verbose_name="contenido"),
        ),
        migrations.AlterField(
            model_name="article",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="articles",
                to="articles.category",
                verbose_name="categoría",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="status",
            field=models.CharField(
                choices=[
                    ("borrador", "Borrador"),
                    ("publicado", "Publicado"),
                    ("archivado", "Archivado"),
                ],
                default="borrador",
                max_length=12,
                verbose_name="estado",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="visibility",
            field=models.CharField(
                choices=[("empresa", "Usuarios de la empresa"), ("soporte", "Solo soporte")],
                default="soporte",
                max_length=16,
                verbose_name="visibilidad",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="author_id",
            field=models.UUIDField(
                blank=True,
                help_text="UUID externo de Accesos; no es el ID del usuario staff de este admin.",
                null=True,
                verbose_name="ID del autor",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="created_at",
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False, verbose_name="creado en"
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="actualizado en"),
        ),
        migrations.AlterField(
            model_name="article",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="publicado en"),
        ),
        migrations.AlterField(
            model_name="article",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="archivado en"),
        ),
    ]
