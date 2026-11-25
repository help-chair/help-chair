// API de Incidencias. Contrato: contracts/incidents/openapi.yaml (Equipo 4).
import { apiGet, apiPatch, apiPost } from './client'

const BASE = '/api/incidents/v1'

export type Impact = 'alto' | 'medio' | 'bajo'
export type Urgency = 'alta' | 'media' | 'baja'
export type Priority = 'P1' | 'P2' | 'P3' | 'P4'
export type IncidentStatus =
  | 'nuevo'
  | 'asignado'
  | 'en_proceso'
  | 'en_espera'
  | 'resuelto'
  | 'cerrado'
  | 'rechazado'
  | 'cancelado'
  | 'reabierto'

export interface Incident {
  id: number
  code: string
  title: string
  description?: string
  impact: Impact
  urgency: Urgency
  priority: Priority
  status?: IncidentStatus
  affected_service?: string
  reported_by: string
  assigned_to?: string
  assignment_group?: string
  source_event_id?: string
  problem_id?: string
  sla_due_at?: string | null
  created_at: string
  updated_at: string
  resolved_at?: string | null
  closed_at?: string | null
}

export interface PaginatedIncidentList {
  count: number
  next: string | null
  previous: string | null
  results: Incident[]
}

export interface IncidentCreateInput {
  title: string
  description?: string
  impact: Impact
  urgency: Urgency
  affected_service?: string
  reported_by: string
  assigned_to?: string
  assignment_group?: string
  source_event_id?: string
  problem_id?: string
}

export type IncidentPatchInput = Partial<IncidentCreateInput> & {
  status?: IncidentStatus
}

export function listarIncidentes(
  filtros: { status?: IncidentStatus; priority?: Priority; assigned_to?: string } = {},
) {
  const query = new URLSearchParams()
  if (filtros.status) query.set('status', filtros.status)
  if (filtros.priority) query.set('priority', filtros.priority)
  if (filtros.assigned_to) query.set('assigned_to', filtros.assigned_to)
  const sufijo = query.toString()
  return apiGet<PaginatedIncidentList>(`${BASE}/incidents/${sufijo ? `?${sufijo}` : ''}`)
}

export function crearIncidente(datos: IncidentCreateInput) {
  return apiPost<Incident>(`${BASE}/incidents/`, datos)
}

export function actualizarIncidente(id: number, datos: IncidentPatchInput) {
  return apiPatch<Incident>(`${BASE}/incidents/${id}/`, datos)
}
