// API de Eventos. Contrato: contracts/events/openapi.yaml (Equipo 1).
// Las rutas completas viven en `/api/events/v1` (el gateway resuelve la empresa por el `Host`).
import { apiGet } from './client'

const BASE = '/api/events/v1'

export type EventOrigin = 'USER' | 'SYSTEM'
export type EventType = 'INFORMATION' | 'WARNING' | 'EXCEPTION'
export type EventCategory = 'SECURITY' | 'REQUEST' | 'FAILURE' | 'CHANGE' | 'GENERAL'
export type EventState =
  | 'NEW'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'ON_HOLD'
  | 'RESOLVED'
  | 'CLOSED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'REOPENED'
export type Priority = 'P1' | 'P2' | 'P3' | 'P4'
export type Destination =
  | 'LOG_ONLY'
  | 'SOLUTION_AUTHOR'
  | 'EVENTS'
  | 'ACCESS'
  | 'REQUESTS'
  | 'INCIDENTS'
  | 'PROBLEMS'

/** Elemento de la lista (`GET /events`), esquema `EventListItem`. */
export interface EventListItem {
  id: string
  origin: EventOrigin
  event_type: EventType
  category: EventCategory
  title: string
  priority: Priority | null
  state: EventState
  service_code: string | null
  destination: Destination | null
  assigned_to_ref: string | null
  occurrence_count: number
  last_seen_at: string
  resolution_due_at: string | null
  created_at: string
}

/** Respuesta paginada de `GET /events`. */
export interface EventPage {
  count: number
  next: string | null
  previous: string | null
  results: EventListItem[]
}

export interface EventosFiltros {
  state?: EventState
  event_type?: EventType
  category?: EventCategory
  priority?: Priority
  origin?: EventOrigin
  service_code?: string
  assigned_to_ref?: string
  open?: boolean
  search?: string
  ordering?: string
}

export function listarEventos(filtros: EventosFiltros = {}) {
  const query = new URLSearchParams()
  if (filtros.state) query.set('state', filtros.state)
  if (filtros.event_type) query.set('event_type', filtros.event_type)
  if (filtros.category) query.set('category', filtros.category)
  if (filtros.priority) query.set('priority', filtros.priority)
  if (filtros.origin) query.set('origin', filtros.origin)
  if (filtros.service_code) query.set('service_code', filtros.service_code)
  if (filtros.assigned_to_ref) query.set('assigned_to_ref', filtros.assigned_to_ref)
  if (filtros.open !== undefined) query.set('open', String(filtros.open))
  if (filtros.search) query.set('search', filtros.search)
  if (filtros.ordering) query.set('ordering', filtros.ordering)
  const sufijo = query.toString()
  return apiGet<EventPage>(`${BASE}/events${sufijo ? `?${sufijo}` : ''}`)
}
