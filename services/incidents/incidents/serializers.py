from rest_framework import serializers

from .models import Incident, Status


class IncidentSerializer(serializers.ModelSerializer):
    code = serializers.CharField(
        read_only=True, help_text="Identificador legible del incidente, p. ej. INC-000042."
    )

    class Meta:
        model = Incident
        fields = [
            "id",
            "code",
            "title",
            "description",
            "impact",
            "urgency",
            "priority",
            "status",
            "affected_service",
            "reported_by",
            "assigned_to",
            "assignment_group",
            "source_event_id",
            "problem_id",
            "sla_due_at",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]
        read_only_fields = [
            "priority",
            "sla_due_at",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]
        extra_kwargs = {
            "status": {
                "help_text": "Estado ITIL. Al crear siempre es «nuevo»; después solo puede "
                "cambiar siguiendo las transiciones permitidas.",
            },
        }

    def validate(self, attrs):
        new_status = attrs.get("status")
        if self.instance is None:
            # Un incidente siempre nace en estado Nuevo.
            if new_status not in (None, Status.NEW):
                raise serializers.ValidationError(
                    {"status": "Un incidente nuevo siempre empieza en estado «nuevo»."}
                )
            return attrs

        if new_status and new_status != self.instance.status:
            if not self.instance.can_transition_to(new_status):
                raise serializers.ValidationError(
                    {"status": f"No se puede pasar de «{self.instance.status}» a «{new_status}»."}
                )
            assigned_to = attrs.get("assigned_to", self.instance.assigned_to)
            if new_status == Status.ASSIGNED and not assigned_to:
                raise serializers.ValidationError(
                    {"assigned_to": "Para pasar a «asignado» hace falta un agente."}
                )
        return attrs
