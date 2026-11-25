// Integración del módulo de Incidencias con services/incidents (contracts/incidents/openapi.yaml).
// Sin datos de ejemplo: si el servicio no responde, la pantalla muestra el error y permite reintentar.
import {
  actualizarIncidente,
  crearIncidente,
  listarIncidentes,
  type Incident,
  type IncidentPatchInput,
  type IncidentStatus,
} from '@/api/incidents'
import type { Escalation, EscalationLevel, NewTicketInput, Priority, Ticket } from './types'

const PRIORIDAD: Record<Incident['priority'], Priority> = {
  P1: 'urgente',
  P2: 'alta',
  P3: 'media',
  P4: 'baja',
}

/** Estados que la tabla muestra como «cerrado» (ya no admiten escalar ni cerrar). */
const ESTADOS_CERRADOS: IncidentStatus[] = ['resuelto', 'cerrado', 'rechazado', 'cancelado']

/**
 * El nivel de escalamiento se guarda en `assignment_group`: escalar reasigna el incidente al
 * grupo del nivel siguiente. Cualquier otro grupo (o ninguno) cuenta como Nivel 1.
 */
export const GRUPO_NIVEL: Record<EscalationLevel, string> = {
  1: 'nivel-1',
  2: 'nivel-2',
  3: 'nivel-3',
}

function nivelDe(grupo?: string): EscalationLevel {
  if (grupo === GRUPO_NIVEL[3]) return 3
  if (grupo === GRUPO_NIVEL[2]) return 2
  return 1
}

/**
 * El contrato no tiene canal, nombre del solicitante ni evidencia: se usan valores por defecto
 * (el nombre visible es `reported_by`). La prioridad la calcula el servicio con impacto × urgencia.
 */
export function incidenteATicket(inc: Incident): Ticket {
  const estadoItil = inc.status ?? 'nuevo'
  const cerrado = ESTADOS_CERRADOS.includes(estadoItil)
  return {
    id: inc.code || String(inc.id),
    apiId: inc.id,
    estadoItil,
    assignedTo: inc.assigned_to || undefined,
    createdAt: inc.created_at,
    requesterId: inc.reported_by,
    requesterName: inc.reported_by || 'Sin nombre',
    channel: 'email',
    description: inc.description || inc.title,
    urgency: inc.urgency,
    priority: PRIORIDAD[inc.priority] ?? 'media',
    impact: inc.impact,
    status: cerrado ? 'cerrado' : 'abierto',
    level: nivelDe(inc.assignment_group),
    closedAt: cerrado ? (inc.closed_at ?? inc.resolved_at ?? inc.updated_at) : undefined,
  }
}

/** Avisos de llamada de los incidentes abiertos que ya están en Nivel 2 o 3. */
function avisosDeEscalamiento(incidentes: Incident[], tickets: Ticket[]): Escalation[] {
  return tickets.flatMap((ticket, indice): Escalation[] =>
    ticket.status === 'abierto' && ticket.level > 1
      ? [
          {
            id: `ESC-${ticket.id}-${ticket.level}`,
            ticketId: ticket.id,
            level: ticket.level as Escalation['level'],
            escalatedAt: incidentes[indice].updated_at,
          },
        ]
      : [],
  )
}

/** GET /incidents/ (primera página: hasta 50 incidentes, ordenados por prioridad y fecha). */
export async function cargarIncidentes(): Promise<{
  tickets: Ticket[]
  escalations: Escalation[]
}> {
  const pagina = await listarIncidentes()
  const tickets = pagina.results.map(incidenteATicket)
  return { tickets, escalations: avisosDeEscalamiento(pagina.results, tickets) }
}

/** POST /incidents/: el servicio asigna el código, el estado «nuevo» y la prioridad. */
export async function registrarIncidente(input: NewTicketInput): Promise<Ticket> {
  const creado = await crearIncidente({
    title: input.description.slice(0, 200),
    description: input.description,
    impact: input.impact,
    urgency: input.urgency,
    reported_by: input.requesterId,
    assignment_group: GRUPO_NIVEL[1],
  })
  // Lo que el contrato aún no guarda se conserva en pantalla durante la sesión.
  return {
    ...incidenteATicket(creado),
    requesterName: input.requesterName,
    channel: input.channel,
    evidenceName: input.evidenceName,
  }
}

/** PATCH /incidents/{id}/: reasigna el incidente al grupo del nivel siguiente. */
export async function escalarIncidente(ticket: Ticket): Promise<Ticket> {
  const nivel = (ticket.level + 1) as EscalationLevel
  const actualizado = await actualizarIncidente(ticket.apiId, {
    assignment_group: GRUPO_NIVEL[nivel],
  })
  return conservarDatosDeSesion(ticket, incidenteATicket(actualizado))
}

/**
 * Pasos para cerrar según las transiciones del servicio (services/incidents/incidents/models.py):
 * un incidente se resuelve y luego se cierra; si aún no tenía agente, se asigna a quien lo cierra.
 */
const RUTA_CIERRE: Partial<Record<IncidentStatus, IncidentStatus[]>> = {
  nuevo: ['asignado', 'en_proceso', 'resuelto', 'cerrado'],
  asignado: ['en_proceso', 'resuelto', 'cerrado'],
  reabierto: ['en_proceso', 'resuelto', 'cerrado'],
  en_espera: ['en_proceso', 'resuelto', 'cerrado'],
  en_proceso: ['resuelto', 'cerrado'],
  resuelto: ['cerrado'],
}

/** PATCH /incidents/{id}/ las veces necesarias hasta dejarlo en «cerrado». */
export async function cerrarIncidente(ticket: Ticket, agenteId?: string): Promise<Ticket> {
  const pasos = RUTA_CIERRE[ticket.estadoItil] ?? []
  let actual = ticket
  for (const estado of pasos) {
    const cambios: IncidentPatchInput = { status: estado }
    if (estado === 'asignado') {
      const agente = ticket.assignedTo ?? agenteId
      if (!agente) {
        throw new Error('Para cerrar el incidente hace falta un agente asignado.')
      }
      cambios.assigned_to = agente
    }
    actual = conservarDatosDeSesion(
      ticket,
      incidenteATicket(await actualizarIncidente(ticket.apiId, cambios)),
    )
  }
  return actual
}

function conservarDatosDeSesion(anterior: Ticket, nuevo: Ticket): Ticket {
  return {
    ...nuevo,
    requesterName: anterior.requesterName,
    channel: anterior.channel,
    evidenceName: anterior.evidenceName,
  }
}
