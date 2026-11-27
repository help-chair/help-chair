from rest_framework.routers import SimpleRouter

from problems.views import KnownErrorViewSet, ProblemViewSet

router = SimpleRouter()
# "problemas" y "errores-conocidos" son rutas del contrato; el basename solo nombra las URL.
router.register("problemas", ProblemViewSet, basename="problem")
router.register("errores-conocidos", KnownErrorViewSet, basename="known-error")

urlpatterns = router.urls
