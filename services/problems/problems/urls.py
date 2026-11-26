from rest_framework.routers import SimpleRouter

from problems.views import ProblemViewSet

router = SimpleRouter()
# "problemas" es la ruta del contrato; el basename solo nombra las URL internamente.
router.register("problemas", ProblemViewSet, basename="problem")

urlpatterns = router.urls
