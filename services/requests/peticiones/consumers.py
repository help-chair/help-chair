import json
import logging
from typing import Any

from django.db import transaction

from .models import Peticion, ServicioSolicitable

logger = logging.getLogger(__name__)

SERVICIO_POR_DEFECTO = "Atención automática de eventos"
SOLICITANTE_SISTEMA_ID = 0


class EventoInvalidoError(ValueError):
    """El payload recibido desde el broker no cumple con los campos mínimos."""


def _extraer_entero_positivo(valor: Any, campo: str, *, obligatorio: bool = False) -> int | None:
    if valor is None or valor == "":
        if obligatorio:
            raise EventoInvalidoError(f"Falta el campo obligatorio '{campo}'.")
        return None
    if isinstance(valor, bool):
        raise EventoInvalidoError(f"El campo '{campo}' debe ser un entero válido.")
    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise EventoInvalidoError(f"El campo '{campo}' debe ser un entero válido.") from exc
    if numero <= 0:
        raise EventoInvalidoError(f"El campo '{campo}' debe ser mayor a cero.")
    return numero


def _resolver_servicio(nombre_servicio: str | None) -> ServicioSolicitable:
    if nombre_servicio:
        existente = ServicioSolicitable.objects.filter(
            nombre__iexact=nombre_servicio.strip(), activo=True
        ).first()
        if existente is not None:
            return existente

    servicio, _ = ServicioSolicitable.objects.get_or_create(
        nombre=SERVICIO_POR_DEFECTO,
        defaults={
            "descripcion": "Servicio base para peticiones generadas automáticamente por eventos.",
            "activo": True,
        },
    )
    return servicio


@transaction.atomic
def procesar_evento_enrutado(payload: dict[str, Any]) -> tuple[Peticion, bool]:
    """Crea una Peticion idempotente a partir de un evento enrutado por services/events.

    Retorna `(peticion, creada)`, donde `creada` es False si el `evento_id` ya existía.
    """
    if not isinstance(payload, dict):
        raise EventoInvalidoError("El mensaje debe ser un objeto JSON.")

    datos = payload.get("datos") if isinstance(payload.get("datos"), dict) else {}

    evento_id = _extraer_entero_positivo(
        payload.get("evento_id") or payload.get("id") or datos.get("evento_id"),
        "evento_id",
        obligatorio=True,
    )

    existente = Peticion.objects.select_for_update().filter(evento_id=evento_id).first()
    if existente is not None:
        logger.info(
            "Evento duplicado omitido",
            extra={"evento_id": evento_id, "peticion_id": str(existente.id)},
        )
        return existente, False

    tipo_evento = str(payload.get("tipo") or "evento.sistema").strip()
    titulo_crudo = str(
        payload.get("titulo")
        or datos.get("titulo")
        or payload.get("descripcion")
        or f"Evento automático: {tipo_evento}"
    ).strip()
    titulo = titulo_crudo[:150]

    descripcion_partes = []
    if payload.get("descripcion"):
        descripcion_partes.append(str(payload["descripcion"]).strip())
    if datos:
        datos_json = json.dumps(datos, ensure_ascii=False)
        descripcion_partes.append(f"Datos del evento ({tipo_evento}): {datos_json}")
    descripcion = "\n".join(descripcion_partes)

    solicitante_crudo = (
        payload.get("solicitante_id")
        if payload.get("solicitante_id") is not None
        else datos.get("usuario_id")
    )
    solicitante_id = (
        _extraer_entero_positivo(solicitante_crudo, "solicitante_id")
        if solicitante_crudo is not None
        else SOLICITANTE_SISTEMA_ID
    )

    nombre_servicio = payload.get("servicio") or datos.get("servicio")
    servicio = _resolver_servicio(str(nombre_servicio) if nombre_servicio else None)

    peticion = Peticion.objects.create(
        tipo=Peticion.Tipo.SERVICIO,
        servicio=servicio,
        titulo=titulo,
        descripcion=descripcion,
        solicitante_id=solicitante_id,
        evento_id=evento_id,
    )
    logger.info(
        "Petición creada desde evento",
        extra={"evento_id": evento_id, "peticion_id": str(peticion.id), "tipo_evento": tipo_evento},
    )
    return peticion, True