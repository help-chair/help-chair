from django.contrib import admin
from django.forms import ModelForm
from django.utils import timezone

from .models import Article, Category


class ArticleAdminForm(ModelForm):
    class Meta:
        model = Article
        fields = ("title", "content", "category", "status", "visibility", "author_id")

    def clean(self):
        data = super().clean()
        status = data.get("status")
        if self.instance._state.adding and status != Article.Status.DRAFT:
            self.add_error("status", "Crea primero un borrador y luego completa su publicación.")
        elif status:
            now = timezone.now()
            if status == Article.Status.PUBLISHED and self.instance.status != status:
                self.instance.published_at = now
            if status == Article.Status.ARCHIVED:
                if self.instance.status != status:
                    self.instance.archived_at = now
            else:
                self.instance.archived_at = None
        return data


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")

    def get_readonly_fields(self, request, obj=None):
        return ("code", "created_at", "updated_at") if obj else ("created_at", "updated_at")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ("title", "id", "status", "visibility", "category", "updated_at")
    list_filter = ("status", "visibility", "category")
    search_fields = ("title", "content")
    readonly_fields = ("id", "created_at", "updated_at", "published_at", "archived_at")
    fields = (
        "id",
        "title",
        "content",
        "category",
        "status",
        "visibility",
        "author_id",
        "created_at",
        "updated_at",
        "published_at",
        "archived_at",
    )

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (("author_id",) if obj and obj.author_id else ())

    def has_delete_permission(self, request, obj=None):
        # No podemos saber qué otros servicios conservan una referencia a este UUID.
        return False
