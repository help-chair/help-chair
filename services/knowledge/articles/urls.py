from rest_framework.routers import SimpleRouter

from articles.views import ArticleViewSet

router = SimpleRouter()
# "articulos" es la ruta del contrato; el basename solo nombra las URL internamente.
router.register("articulos", ArticleViewSet, basename="article")

urlpatterns = router.urls
