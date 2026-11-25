// Tipos del módulo de Incidencias (ITIL v4 · Incident Management).
// Los del contrato (contracts/incidents/openapi.yaml) viven en src/api/incidents.ts; estos son
// los de la vista, que se arman a partir de un `Incident` en features/incidents/api.ts.
import type { IncidentStatus } from '@/api/incidents'

export type Channel = 'email' | 'telefono'
export type Urgency = 'alta' | 'media' | 'baja'
export type Priority = 'urgente' | 'alta' | 'media' | 'baja'
export type Impact = 'alto' | 'medio' | 'bajo'
export type TicketStatus = 'abierto' | 'cerrado'

/** Nivel de soporte que atiende el caso. Al escalar sube un nivel, hasta el 3. */
export type EscalationLevel = 1 | 2 | 3

export interface Ticket {
  /** Código legible del contrato (`code`, p. ej. INC-000042). */
  id: string
  /** `id` numérico del contrato: es el que usan las rutas `/incidents/{id}/`. */
  apiId: number
  /** Estado ITIL real del servicio; `status` es su versión simplificada para la tabla. */
  estadoItil: IncidentStatus
  /** Agente asignado (`assigned_to`), si lo hay. */
  assignedTo?: string
  /** Fecha de registro en formato ISO 8601. */
  createdAt: string
  requesterId: string
  requesterName: string
  channel: Channel
  description: string
  urgency: Urgency
  priority: Priority
  impact: Impact
  status: TicketStatus
  level: EscalationLevel
  /** Nombre del archivo de evidencia, si se adjuntó. */
  evidenceName?: string
  /** Fecha de cierre en formato ISO 8601. */
  closedAt?: string
}

/** Aviso para que Incidentes llame a un cargo mayor porque un nivel no resolvió el caso. */
export interface Escalation {
  id: string
  ticketId: string
  level: Exclude<EscalationLevel, 1>
  /** Fecha del escalamiento en formato ISO 8601. */
  escalatedAt: string
  /** Fecha en que Incidentes hizo la llamada; vacía mientras siga pendiente. */
  calledAt?: string
}

/** Lo que captura el modal «Abrir ticket»; el resto lo completa el sistema al registrar. */
export type NewTicketInput = Pick<
  Ticket,
  | 'requesterId'
  | 'requesterName'
  | 'channel'
  | 'description'
  | 'urgency'
  | 'priority'
  | 'impact'
  | 'evidenceName'
>
