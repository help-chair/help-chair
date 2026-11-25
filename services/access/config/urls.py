from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.activation import BootstrapAdminView

urlpatterns = [
    path("health/", include("core.urls")),
    path("api/access/v1/", include("core.auth_urls")),
    # No se expone en el ingress: solo lo alcanza el aprovisionador.
    path(
        "internal/v1/bootstrap-admin",
        BootstrapAdminView.as_view(),
        name="interno-bootstrap-admin",
    ),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
