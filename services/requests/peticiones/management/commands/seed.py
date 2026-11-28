from django.core.management.base import BaseCommand
from django.utils import timezone

from peticiones.models import CatalogItem, ServiceRequest


class Command(BaseCommand):
    help = "Carga datos de ejemplo idempotentes para catálogo y peticiones (dev/testing)."

    def handle(self, *args, **options):
        catalog_specs = [
            {
                "name": "Alta de correo corporativo",
                "description": "Creación de buzón institucional y alias de departamento.",
                "is_active": True,
            },
            {
                "name": "Acceso a VPN corporativa",
                "description": "Habilitación de perfil VPN y segundo factor de autenticación.",
                "is_active": True,
            },
            {
                "name": "Instalación de software autorizado",
                "description": "Despliegue de herramientas de desarrollo o productividad.",
                "is_active": True,
            },
            {
                "name": "Servicio legado descontinuado",
                "description": "Elemento inactivo para verificar filtros de catálogo.",
                "is_active": False,
            },
        ]

        catalog_by_name = {}
        for spec in catalog_specs:
            item, _ = CatalogItem.objects.update_or_create(
                name=spec["name"],
                defaults={
                    "description": spec["description"],
                    "is_active": spec["is_active"],
                },
            )
            catalog_by_name[item.name] = item

        sample_requests = [
            {
                "event_id": "seed-req-001",
                "request_type": ServiceRequest.RequestType.SERVICE,
                "approval_status": ServiceRequest.ApprovalStatus.NOT_REQUIRED,
                "service": catalog_by_name["Alta de correo corporativo"],
                "title": "Alta de correo para nuevo ingreso de soporte",
                "description": "Solicitado durante onboarding del área de operaciones.",
                "status": ServiceRequest.Status.NEW,
                "requester_id": "usuario-demo-101",
                "assignee_id": "",
                "closed_at": None,
            },
            {
                "event_id": "seed-req-002",
                "request_type": ServiceRequest.RequestType.SERVICE,
                "approval_status": ServiceRequest.ApprovalStatus.NOT_REQUIRED,
                "service": catalog_by_name["Acceso a VPN corporativa"],
                "title": "Acceso VPN para guardia nocturna",
                "description": "Requiere conexión al clúster de testing.",
                "status": ServiceRequest.Status.IN_PROGRESS,
                "requester_id": "usuario-demo-102",
                "assignee_id": "agente-demo-201",
                "closed_at": None,
            },
            {
                "event_id": "seed-req-003",
                "request_type": ServiceRequest.RequestType.SERVICE,
                "approval_status": ServiceRequest.ApprovalStatus.NOT_REQUIRED,
                "service": catalog_by_name["Instalación de software autorizado"],
                "title": "Configuración de Podman Desktop en equipo de QA",
                "description": "Instalado y validado con el usuario.",
                "status": ServiceRequest.Status.CLOSED,
                "requester_id": "usuario-demo-103",
                "assignee_id": "agente-demo-202",
                "closed_at": timezone.now(),
            },
        ]

        for req_spec in sample_requests:
            ServiceRequest.objects.update_or_create(
                event_id=req_spec["event_id"],
                defaults=req_spec,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed aplicado: {CatalogItem.objects.count()} servicios en catálogo y "
                f"{ServiceRequest.objects.count()} peticiones."
            )
        )
