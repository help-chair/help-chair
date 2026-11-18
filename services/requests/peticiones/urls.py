from rest_framework.routers import DefaultRouter

from .views import PeticionViewSet, ServicioSolicitableViewSet

router = DefaultRouter()
router.register("peticiones", PeticionViewSet)
router.register("servicios", ServicioSolicitableViewSet)

urlpatterns = router.urls