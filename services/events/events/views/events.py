from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from ..actors import get_actor_ref
from ..models import (
    TERMINAL_STATES,
    Event,
    EventCategory,
    EventOrigin,
    EventState,
    EventType,
    Priority,
)
from ..pagination import EventLimitOffsetPagination
from ..serializers import (
    ErrorSerializer,
    EventCreateSerializer,
    EventDetailSerializer,
    EventListItemSerializer,
    EventPageSerializer,
    EventReadSerializer,
    EventUpdateSerializer,
)
from ..services import register_event, update_event

ALLOWED_ORDERING = (
    "created_at",
    "-created_at",
    "last_seen_at",
    "-last_seen_at",
    "priority",
    "-priority",
    "resolution_due_at",
    "-resolution_due_at",
)


class EventListCreateView(APIView):
    @extend_schema(
        operation_id="listEvents",
        responses={
            200: EventPageSerializer,
            422: OpenApiResponse(response=ErrorSerializer, description="Datos inválidos"),
        },
        parameters=[
            OpenApiParameter("state", str, enum=[value for value, _ in EventState.choices]),
            OpenApiParameter("event_type", str, enum=[value for value, _ in EventType.choices]),
            OpenApiParameter("category", str, enum=[value for value, _ in EventCategory.choices]),
            OpenApiParameter("priority", str, enum=[value for value, _ in Priority.choices]),
            OpenApiParameter("origin", str, enum=[value for value, _ in EventOrigin.choices]),
            OpenApiParameter("service_code", str),
            OpenApiParameter("assigned_to_ref", str),
            OpenApiParameter("open", bool),
            OpenApiParameter("created_from", OpenApiTypes.DATETIME),
            OpenApiParameter("created_to", OpenApiTypes.DATETIME),
            OpenApiParameter("search", {"type": "string", "maxLength": 100}),
            OpenApiParameter("ordering", str, enum=ALLOWED_ORDERING),
            OpenApiParameter("limit", {"type": "integer", "minimum": 1, "maximum": 200}),
            OpenApiParameter("offset", {"type": "integer", "minimum": 0}),
        ],
    )
    def get(self, request):
        queryset = Event.objects.select_related("service").all()

        enum_filters = {
            "state": dict(EventState.choices),
            "event_type": dict(EventType.choices),
            "category": dict(EventCategory.choices),
            "priority": dict(Priority.choices),
            "origin": dict(EventOrigin.choices),
        }
        for param, valid_values in enum_filters.items():
            value = request.query_params.get(param)
            if value is not None:
                if value not in valid_values:
                    raise ValidationError({param: f'"{value}" no es un valor válido.'})
                queryset = queryset.filter(**{param: value})

        service_code = request.query_params.get("service_code")
        if service_code is not None:
            queryset = queryset.filter(service__code=service_code)

        assigned_to_ref = request.query_params.get("assigned_to_ref")
        if assigned_to_ref is not None:
            queryset = queryset.filter(assigned_to_ref=assigned_to_ref)

        open_filter = request.query_params.get("open")
        if open_filter is not None:
            if open_filter not in ("true", "false"):
                raise ValidationError({"open": '"open" debe ser "true" o "false".'})
            if open_filter == "true":
                queryset = queryset.exclude(state__in=TERMINAL_STATES)
            else:
                queryset = queryset.filter(state__in=TERMINAL_STATES)

        created_from = request.query_params.get("created_from")
        if created_from is not None:
            created_from = self._parse_datetime(created_from, "created_from")
            queryset = queryset.filter(created_at__gte=created_from)

        created_to = request.query_params.get("created_to")
        if created_to is not None:
            created_to = self._parse_datetime(created_to, "created_to")
            queryset = queryset.filter(created_at__lte=created_to)

        search = request.query_params.get("search")
        if search is not None:
            if len(search) > 100:
                raise ValidationError({"search": "Debe tener como máximo 100 caracteres."})
            queryset = queryset.filter(Q(title__icontains=search) | Q(message__icontains=search))

        limit = request.query_params.get("limit")
        if limit is not None:
            try:
                limit_value = int(limit)
            except (TypeError, ValueError):
                raise ValidationError({"limit": "Debe ser un entero."}) from None
            if not 1 <= limit_value <= 200:
                raise ValidationError({"limit": "Debe estar entre 1 y 200."})

        offset = request.query_params.get("offset")
        if offset is not None:
            try:
                offset_value = int(offset)
            except (TypeError, ValueError):
                raise ValidationError({"offset": "Debe ser un entero."}) from None
            if offset_value < 0:
                raise ValidationError({"offset": "Debe ser mayor o igual que cero."})

        ordering = request.query_params.get("ordering", "-created_at")
        if ordering not in ALLOWED_ORDERING:
            raise ValidationError({"ordering": "Valor de ordenación no válido."})

        paginator = EventLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset.order_by(ordering), request, view=self)
        return paginator.get_paginated_response(EventListItemSerializer(page, many=True).data)

    @extend_schema(
        operation_id="registerEvent",
        request=EventCreateSerializer,
        responses={
            201: EventReadSerializer,
            200: EventReadSerializer,
            422: OpenApiResponse(response=ErrorSerializer, description="Datos inválidos"),
        },
    )
    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event, created = register_event(serializer.validated_data, actor_ref=get_actor_ref(request))
        data = EventReadSerializer(event).data
        if created:
            return Response(
                data,
                status=status.HTTP_201_CREATED,
                headers={"Location": f"/api/v1/events/{event.id}"},
            )
        return Response(data, status=status.HTTP_200_OK)

    @staticmethod
    def _parse_datetime(value, field_name):
        try:
            return serializers.DateTimeField().to_internal_value(value)
        except serializers.ValidationError:
            raise ValidationError({field_name: "Debe ser una fecha ISO 8601 válida."}) from None


class EventDetailView(APIView):
    @extend_schema(
        operation_id="getEvent",
        responses={
            200: EventDetailSerializer,
            404: OpenApiResponse(response=ErrorSerializer, description="Evento no encontrado"),
        },
    )
    def get(self, request, id):
        event = get_object_or_404(Event.objects.select_related("service", "source"), id=id)
        return Response(EventDetailSerializer(event).data)

    @extend_schema(
        operation_id="updateEvent",
        request=EventUpdateSerializer,
        responses={
            200: EventReadSerializer,
            404: OpenApiResponse(response=ErrorSerializer, description="Evento no encontrado"),
            409: OpenApiResponse(response=ErrorSerializer, description="Conflicto de estado"),
            422: OpenApiResponse(response=ErrorSerializer, description="Datos inválidos"),
        },
    )
    def patch(self, request, id):
        event = get_object_or_404(Event.objects.select_related("service", "source"), id=id)
        serializer = EventUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = update_event(event, serializer.validated_data, actor_ref=get_actor_ref(request))
        event = Event.objects.select_related("service", "source").get(pk=event.pk)
        return Response(EventReadSerializer(event).data)
