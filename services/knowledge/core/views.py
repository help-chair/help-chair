import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def check_database() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")


@require_GET
def live(request):
    """Liveness: el proceso responde."""
    return JsonResponse({"status": "ok"})


@require_GET
def ready(request):
    """Readiness: el proceso responde Y la base de datos es alcanzable."""
    try:
        check_database()
    except Exception:
        logger.warning("readiness_database_unavailable")
        return JsonResponse({"status": "unavailable", "database": "down"}, status=503)
    return JsonResponse({"status": "ok", "database": "up"})
