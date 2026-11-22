from rest_framework.routers import DefaultRouter

from .views import IncidentViewSet

router = DefaultRouter(trailing_slash=True)
router.register("incidents", IncidentViewSet, basename="incident")

urlpatterns = router.urls
