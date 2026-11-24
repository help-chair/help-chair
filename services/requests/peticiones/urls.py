from rest_framework.routers import DefaultRouter

from .views import CatalogItemViewSet, ServiceRequestViewSet

router = DefaultRouter()
router.register("peticiones", ServiceRequestViewSet)
router.register("servicios", CatalogItemViewSet)

urlpatterns = router.urls