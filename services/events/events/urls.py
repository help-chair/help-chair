from django.urls import path  # noqa: F401

from .views import EventDetailView, EventHistoryView, EventListCreateView, EventTransitionsView

app_name = "events"

# Endpoints de la API de eventos (montados en /api/v1/).
urlpatterns = [
    path("events", EventListCreateView.as_view(), name="event-list"),
    path("events/<uuid:id>", EventDetailView.as_view(), name="event-detail"),
    path("events/<uuid:id>/transitions", EventTransitionsView.as_view(), name="event-transitions"),
    path("events/<uuid:id>/history", EventHistoryView.as_view(), name="event-history"),
]
