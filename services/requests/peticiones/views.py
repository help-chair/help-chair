from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import CatalogItem, ServiceRequest
from .permissions import (
    REQUESTER_STATUS_CHANGES,
    can_attend,
    jwt_enabled,
    token_user_id,
)
from .serializers import (
    ApproveChangeSerializer,
    AssignRequestSerializer,
    CatalogItemSerializer,
    RejectChangeSerializer,
    SatisfactionSurveySerializer,
    ServiceRequestSerializer,
    StatusChangeSerializer,
)

ASSIGNABLE_STATUSES = (
    ServiceRequest.Status.NEW,
    ServiceRequest.Status.ASSIGNED,
    ServiceRequest.Status.IN_PROGRESS,
    ServiceRequest.Status.REOPENED,
)

ERROR_400 = OpenApiResponse(description="Datos o parámetros de consulta inválidos.")
ERROR_404 = OpenApiResponse(description="Recurso no encontrado.")
ERROR_409 = OpenApiResponse(description="La petición ya tiene una encuesta respondida.")

SURVEY_STATUSES = (ServiceRequest.Status.RESOLVED, ServiceRequest.Status.CLOSED)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="incluir_inactivos",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Si es true, incluye servicios desactivados en el listado.",
            ),
        ],
        responses={200: CatalogItemSerializer(many=True), 400: ERROR_400},
    ),
    create=extend_schema(responses={201: CatalogItemSerializer, 400: ERROR_400}),
    retrieve=extend_schema(responses={200: CatalogItemSerializer, 404: ERROR_404}),
    update=extend_schema(responses={200: CatalogItemSerializer, 400: ERROR_400, 404: ERROR_404}),
    partial_update=extend_schema(
        responses={200: CatalogItemSerializer, 400: ERROR_400, 404: ERROR_404}
    ),
    destroy=extend_schema(responses={204: None, 404: ERROR_404}),
)
class CatalogItemViewSet(viewsets.ModelViewSet):
    queryset = CatalogItem.objects.all()
    serializer_class = CatalogItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            raw_flag = self.request.query_params.get("incluir_inactivos")
            if raw_flag is None or raw_flag == "":
                include_inactive = False
            elif raw_flag.lower() in ("true", "1"):
                include_inactive = True
            elif raw_flag.lower() in ("false", "0"):
                include_inactive = False
            else:
                raise ValidationError(
                    {"incluir_inactivos": "Debe ser un booleano válido (true o false)."}
                )

            if not include_inactive:
                queryset = queryset.filter(is_active=True)
        return queryset


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="estado",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[choice[0] for choice in ServiceRequest.Status.choices],
                description="Filtrar peticiones por estado.",
            ),
            OpenApiParameter(
                name="tipo",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[choice[0] for choice in ServiceRequest.RequestType.choices],
                description="Filtrar peticiones por tipo (servicio o cambio).",
            ),
            OpenApiParameter(
                name="estado_aprobacion",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[choice[0] for choice in ServiceRequest.ApprovalStatus.choices],
                description="Filtrar solicitudes de cambio por estado de aprobación.",
            ),
            OpenApiParameter(
                name="asignado_a_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar peticiones por ID (Accesos) del agente asignado.",
            ),
            OpenApiParameter(
                name="solicitante_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar peticiones por ID (Accesos) del usuario solicitante.",
            ),
        ],
        responses={200: ServiceRequestSerializer(many=True), 400: ERROR_400},
    ),
    create=extend_schema(responses={201: ServiceRequestSerializer, 400: ERROR_400}),
    retrieve=extend_schema(responses={200: ServiceRequestSerializer, 404: ERROR_404}),
    update=extend_schema(responses={200: ServiceRequestSerializer, 400: ERROR_400, 404: ERROR_404}),
    partial_update=extend_schema(
        responses={200: ServiceRequestSerializer, 400: ERROR_400, 404: ERROR_404}
    ),
    destroy=extend_schema(responses={204: None, 404: ERROR_404}),
)
class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.select_related("survey")
    serializer_class = ServiceRequestSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # El usuario final solo ve sus peticiones; las demás responden 404.
        if not can_attend(self.request):
            queryset = queryset.filter(requester_id=token_user_id(self.request))
        params = self.request.query_params

        status_param = params.get("estado")
        if status_param:
            if status_param not in ServiceRequest.Status.values:
                raise ValidationError({"estado": "Estado no válido."})
            queryset = queryset.filter(status=status_param)

        type_param = params.get("tipo")
        if type_param:
            if type_param not in ServiceRequest.RequestType.values:
                raise ValidationError({"tipo": "Tipo de petición no válido."})
            queryset = queryset.filter(request_type=type_param)

        approval_param = params.get("estado_aprobacion")
        if approval_param:
            if approval_param not in ServiceRequest.ApprovalStatus.values:
                raise ValidationError({"estado_aprobacion": "Estado de aprobación no válido."})
            queryset = queryset.filter(approval_status=approval_param)

        filter_map = {
            "asignado_a_id": "assignee_id",
            "solicitante_id": "requester_id",
        }
        for query_key, model_field in filter_map.items():
            raw_value = params.get(query_key)
            if raw_value:
                queryset = queryset.filter(**{model_field: raw_value})

        return queryset

    def perform_create(self, serializer):
        # Con JWT, el usuario final siempre crea a su nombre: el solicitante sale del token.
        if jwt_enabled() and not can_attend(self.request):
            serializer.save(requester_id=token_user_id(self.request))
        else:
            serializer.save()

    @extend_schema(
        request=StatusChangeSerializer,
        responses={200: ServiceRequestSerializer, 400: ERROR_400, 404: ERROR_404},
    )
    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def change_status(self, request, pk=None):
        service_request = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        next_status = serializer.validated_data["estado"]

        if not can_attend(request) and next_status not in REQUESTER_STATUS_CHANGES:
            raise PermissionDenied(
                "Como solicitante solo puedes cancelar, cerrar o reabrir tu petición."
            )

        if (
            service_request.requires_approval
            and next_status in {ServiceRequest.Status.IN_PROGRESS, ServiceRequest.Status.RESOLVED}
            and service_request.approval_status != ServiceRequest.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "La solicitud de cambio requiere aprobación antes de pasar "
                        f"a {next_status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not service_request.can_transition_to(next_status):
            return Response(
                {"detail": (f"No se puede pasar de {service_request.status} a {next_status}.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.status = next_status
        if next_status == ServiceRequest.Status.CANCELLED:
            service_request.cancellation_reason = serializer.validated_data["motivo_cancelacion"]
        if next_status == ServiceRequest.Status.CLOSED:
            service_request.closed_at = timezone.now()
        service_request.save()
        return Response(ServiceRequestSerializer(service_request).data)

    @extend_schema(
        request=SatisfactionSurveySerializer,
        responses={
            201: SatisfactionSurveySerializer,
            400: ERROR_400,
            404: ERROR_404,
            409: ERROR_409,
        },
        description=(
            "El solicitante califica la atención (1 a 5) cuando la petición está resuelta "
            "o cerrada. Si estaba resuelta, la petición pasa a cerrada."
        ),
    )
    @action(detail=True, methods=["post"], url_path="encuesta")
    def survey(self, request, pk=None):
        service_request = self.get_object()
        if jwt_enabled() and service_request.requester_id != token_user_id(request):
            raise PermissionDenied("Solo quien hizo la petición puede calificarla.")

        serializer = SatisfactionSurveySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if service_request.status not in SURVEY_STATUSES:
            return Response(
                {"detail": "Solo se puede calificar una petición resuelta o cerrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        respondent_id = token_user_id(request) if jwt_enabled() else service_request.requester_id
        try:
            with transaction.atomic():
                survey = serializer.save(
                    service_request=service_request, respondent_id=respondent_id
                )
                if service_request.status == ServiceRequest.Status.RESOLVED:
                    service_request.status = ServiceRequest.Status.CLOSED
                    service_request.closed_at = timezone.now()
                    service_request.save(update_fields=["status", "closed_at", "updated_at"])
        except IntegrityError:
            return Response(
                {"detail": "Esta petición ya tiene una encuesta respondida."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(SatisfactionSurveySerializer(survey).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=AssignRequestSerializer,
        responses={200: ServiceRequestSerializer, 400: ERROR_400, 404: ERROR_404},
    )
    @action(detail=True, methods=["post"], url_path="asignar")
    def assign(self, request, pk=None):
        service_request = self.get_object()
        serializer = AssignRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if service_request.status not in ASSIGNABLE_STATUSES:
            return Response(
                {"detail": f"No se puede asignar en estado {service_request.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.assignee_id = serializer.validated_data["asignado_a_id"]
        if service_request.status in (
            ServiceRequest.Status.NEW,
            ServiceRequest.Status.REOPENED,
        ):
            service_request.status = ServiceRequest.Status.ASSIGNED
        service_request.save()
        return Response(ServiceRequestSerializer(service_request).data)

    @extend_schema(
        request=ApproveChangeSerializer,
        responses={200: ServiceRequestSerializer, 400: ERROR_400, 404: ERROR_404},
    )
    @action(detail=True, methods=["post"], url_path="aprobar")
    def approve(self, request, pk=None):
        service_request = self.get_object()
        serializer = ApproveChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approver_id = _approver_from_token(request, serializer.validated_data["aprobador_id"])

        if not service_request.requires_approval:
            return Response(
                {"detail": "Solo las peticiones de tipo cambio requieren aprobación."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if service_request.approval_status != ServiceRequest.ApprovalStatus.PENDING:
            return Response(
                {
                    "detail": (
                        "La solicitud de cambio no está pendiente de aprobación "
                        f"(estado actual: {service_request.approval_status})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if service_request.approver_id and service_request.approver_id != approver_id:
            return Response(
                {"detail": "El usuario no corresponde al aprobador designado para este cambio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.approver_id = approver_id
        service_request.approval_status = ServiceRequest.ApprovalStatus.APPROVED
        service_request.approved_at = timezone.now()
        service_request.save()
        return Response(ServiceRequestSerializer(service_request).data)

    @extend_schema(
        request=RejectChangeSerializer,
        responses={200: ServiceRequestSerializer, 400: ERROR_400, 404: ERROR_404},
    )
    @action(detail=True, methods=["post"], url_path="rechazar")
    def reject(self, request, pk=None):
        service_request = self.get_object()
        serializer = RejectChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approver_id = _approver_from_token(request, serializer.validated_data["aprobador_id"])

        if not service_request.requires_approval:
            return Response(
                {"detail": "Solo las peticiones de tipo cambio pueden rechazarse."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if service_request.approval_status != ServiceRequest.ApprovalStatus.PENDING:
            return Response(
                {
                    "detail": (
                        "La solicitud de cambio no está pendiente de aprobación "
                        f"(estado actual: {service_request.approval_status})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if service_request.approver_id and service_request.approver_id != approver_id:
            return Response(
                {"detail": "El usuario no corresponde al aprobador designado para este cambio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.approver_id = approver_id
        service_request.approval_status = ServiceRequest.ApprovalStatus.REJECTED
        service_request.rejection_reason = serializer.validated_data["motivo_rechazo"]
        service_request.status = ServiceRequest.Status.CANCELLED
        service_request.cancellation_reason = serializer.validated_data["motivo_rechazo"]
        service_request.closed_at = timezone.now()
        service_request.save()
        return Response(ServiceRequestSerializer(service_request).data)


def _approver_from_token(request, approver_id: str) -> str:
    """Con JWT, nadie aprueba ni rechaza en nombre de otra persona."""
    if jwt_enabled() and approver_id != token_user_id(request):
        raise PermissionDenied("Solo puedes aprobar o rechazar con tu propio usuario.")
    return approver_id
