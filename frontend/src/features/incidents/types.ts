// Tipos del módulo de Incidencias (ITIL v4 · Incident Management).
// Cuando exista contracts/incidents/openapi.yaml, estos tipos deben generarse desde ahí.

export type Channel = 'email' | 'telefono'
export type Urgency = 'alta' | 'media' | 'baja'
export type Priority = 'urgente' | 'alta' | 'media' | 'baja'
export type Impact = 'alto' | 'medio' | 'bajo'
export type TicketStatus = 'abierto' | 'cerrado'

/** Nivel de soporte que atiende el caso. Al escalar sube un nivel, hasta el 3. */
export type EscalationLevel = 1 | 2 | 3

export interface Ticket {
  id: string
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
