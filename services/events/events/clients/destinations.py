"""Un cliente por servicio destino y la fábrica que los construye desde settings."""

from django.conf import settings

from ..models import Destination
from .base import BaseClient, ServiceTokenProvider

IMPACT = {"HIGH": "alto", "MEDIUM": "medio", "LOW": "bajo"}
URGENCY = {"HIGH": "alta", "MEDIUM": "media", "LOW": "baja"}
PROBLEM_PRIORITY = {"P1": "critica", "P2": "alta", "P3": "media", "P4": "baja"}


def _service_code(event):
    return event.service.code if event.service_id else None


class IncidentsClient(BaseClient):
    """Contrato: contracts/incidents (POST /api/incidents/v1/incidents/)."""

    destination = Destination.INCIDENTS
    path = "/api/incidents/v1/incidents/"

    def build_payload(self, event, rule_code):
        description = event.message
        if rule_code == "R9":
            description = (
                "[TRIAGE MANUAL · regla 9] Ninguna regla de destino coincidió; "
                "revisar y clasificar.\n\n" + description
            )
        payload = {
            "title": event.title[:200],
            "description": description,
            "impact": IMPACT.get(event.impact, "medio"),
            "urgency": URGENCY.get(event.urgency, "media"),
            "reported_by": event.reporter_ref or "events-service",
            "source_event_id": str(event.pk),
        }
        if code := _service_code(event):
            payload["affected_service"] = code
        return payload


class ProblemsClient(BaseClient):
    """Contrato: contracts/problems (POST /api/problems/v1/problemas/)."""

    destination = Destination.PROBLEMS
    path = "/api/problems/v1/problemas/"

    def build_payload(self, event, rule_code):
        description = (
            f"{event.message}\n\n"
            f"Evento origen: {event.pk} · regla {rule_code} · "
            f"{event.occurrence_count} ocurrencias (primera: {event.first_seen_at:%Y-%m-%d %H:%M})"
        )
        return {
            "titulo": event.title[:200],
            "descripcion": description,
            "prioridad": PROBLEM_PRIORITY.get(event.priority, "media"),
            "origen": "patron",
        }


class RequestsClient(BaseClient):
    """PROPUESTA: contracts/requests aún no existe (ver tabla de contratos propuestos)."""

    destination = Destination.REQUESTS
    path = "/api/requests/v1/requests/"

    def build_payload(self, event, rule_code):
        return {
            "type": "cambio" if rule_code == "R8" else "catalogo",
            "title": event.title[:200],
            "description": event.message,
            "priority": event.priority or None,
            "service_code": _service_code(event),
            "requested_by": event.reporter_ref or "events-service",
            "source_event_id": str(event.pk),
        }


class AccessClient(BaseClient):
    """PROPUESTA: Accesos aún no expone un endpoint de recepción de eventos de seguridad."""

    destination = Destination.ACCESS
    path = "/api/access/v1/security-events/"

    def build_payload(self, event, rule_code):
        return {
            "source_event_id": str(event.pk),
            "title": event.title[:200],
            "message": event.message,
            "priority": event.priority or None,
            "user_ref": event.reporter_ref or None,
            "occurrence_count": event.occurrence_count,
            "payload": event.payload,
        }


_CLIENTS = {
    Destination.ACCESS: AccessClient,
    Destination.REQUESTS: RequestsClient,
    Destination.INCIDENTS: IncidentsClient,
    Destination.PROBLEMS: ProblemsClient,
}
_token_provider = None


def get_token_provider() -> ServiceTokenProvider:
    global _token_provider
    if _token_provider is None:
        _token_provider = ServiceTokenProvider(
            static_token=settings.SERVICE_JWT,
            access_url=settings.DESTINATION_URLS.get(Destination.ACCESS, ""),
            email=settings.SERVICE_ACCOUNT_EMAIL,
            password=settings.SERVICE_ACCOUNT_PASSWORD,
            timeout=settings.DESTINATION_TIMEOUT,
        )
    return _token_provider


def get_client(destination) -> BaseClient:
    return _CLIENTS[destination](token_provider=get_token_provider())
