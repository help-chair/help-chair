from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from ..actors import get_actor_ref
from ..models import Event
from ..pagination import EventLimitOffsetPagination
from ..serializers import (
    AllowedTransitionsSerializer,
    ErrorSerializer,
    EventHistoryEntrySerializer,
    EventHistoryPageSerializer,
    EventReadSerializer,
    EventTransitionSerializer,
)
from ..services import allowed_transitions, transition_event

NOT_FOUND = OpenApiResponse(response=ErrorSerializer, description="Evento no encontrado")


class EventTransitionsView(APIView):
    @extend_schema(
        operation_id="listAllowedTransitions",
        responses={200: AllowedTransitionsSerializer, 404: NOT_FOUND},
    )
    def get(self, request, id):
        event = get_object_or_404(Event, id=id)
        return Response({"state": event.state, "allowed": allowed_transitions(event)})

    @extend_schema(
        operation_id="transitionEvent",
        request={"application/json": EventTransitionSerializer},
        responses={
            200: EventReadSerializer,
            404: NOT_FOUND,
            409: OpenApiResponse(response=ErrorSerializer, description="Transición no permitida"),
            422: OpenApiResponse(response=ErrorSerializer, description="Datos inválidos"),
        },
    )
    def post(self, request, id):
        event = get_object_or_404(Event.objects.select_related("service", "source"), id=id)
        serializer = EventTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        event = transition_event(
            event,
            data["to_state"],
            actor_ref=get_actor_ref(request),
            reason=data.get("reason", ""),
            closure_code=data.get("closure_code", ""),
        )
        event = Event.objects.select_related("service", "source").get(pk=event.pk)
        return Response(EventReadSerializer(event).data)


class EventHistoryView(APIView):
    @extend_schema(
        operation_id="listEventHistory",
        parameters=[
            OpenApiParameter("limit", {"type": "integer", "minimum": 1, "maximum": 200}),
            OpenApiParameter("offset", {"type": "integer", "minimum": 0}),
        ],
        responses={200: EventHistoryPageSerializer, 404: NOT_FOUND},
    )
    def get(self, request, id):
        event = get_object_or_404(Event, id=id)
        queryset = event.history.order_by("-changed_at", "-id")
        paginator = EventLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(EventHistoryEntrySerializer(page, many=True).data)
