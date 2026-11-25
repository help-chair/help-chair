// Integración del módulo de Incidencias con services/incidents.
// Llama a la API real y, si el servicio no responde, usa los datos de ejemplo.
import { ApiError } from '@/api/client'
import { crearIncidente, listarIncidentes, type Incident } from '@/api/incidents'
import { createSampleData } from './data'
import type { Escalation, NewTicketInput, Priority, Ticket } from './types'

function servicioInalcanzable(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 404 || error.status >= 500
  return true
}

const PRIORIDAD: Record<string, Priority> = {
  P1: 'urgente',
  P2: 'alta',
  P3: 'media',
  P4: 'baja',
}

/**
 * El contrato v0 de Incidencias no tiene los campos que usa la UI actual (canal, nombre del
 * solicitante, nivel de escalamiento ni evidencia). Se mapea lo que hay y el resto usa valores
 * por defecto; la alineación completa del modelo es un refactor pendiente.
 */
function incidenteATicket(inc: Incident): Ticket {
  const cerrado = ['cerrado', 'resuelto', 'rechazado', 'cancelado'].includes(inc.status ?? '')
  return {
    id: inc.code || String(inc.id),
    createdAt: inc.created_at,
    requesterId: inc.reported_by,
    requesterName: inc.reported_by || 'Sin nombre',
    channel: 'email',
    description: inc.description || inc.title,
    urgency: inc.urgency,
    priority: PRIORIDAD[inc.priority] ?? 'media',
    impact: inc.impact,
    status: cerrado ? 'cerrado' : 'abierto',
    level: 1,
    closedAt: cerrado ? (inc.closed_at ?? inc.resolved_at ?? undefined) : undefined,
  }
}

export async function cargarIncidentesConRespaldo(): Promise<{
  tickets: Ticket[]
  escalations: Escalation[]
}> {
  try {
    const pagina = await listarIncidentes()
    return { tickets: pagina.results.map(incidenteATicket), escalations: [] }
  } catch (error) {
    if (!servicioInalcanzable(error)) throw error
    return createSampleData()
  }
}

/** Envía el alta del incidente al contrato OpenAPI v1 sin bloquear la respuesta optimista. */
export async function registrarIncidenteEnApi(input: NewTicketInput): Promise<void> {
  try {
    await crearIncidente({
      title: input.description.slice(0, 200),
      description: input.description,
      impact: input.impact,
      urgency: input.urgency,
      reported_by: input.requesterId,
    })
  } catch (error) {
    if (!servicioInalcanzable(error)) throw error
  }
}
