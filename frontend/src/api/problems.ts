// API de Problemas. Contrato: contracts/problems/openapi.yaml (Equipo 5).
// Las rutas completas son `/api/problems/v1/problemas/` y `/api/problems/v1/errores-conocidos/`.
import { apiGet, apiPost } from './client'
import type {
  CambioEstado,
  ErrorConocido,
  ErrorConocidoCrear,
  Problema,
  ProblemaCrear,
  ProblemaIncidente,
} from '@/features/problems/types'

const BASE = '/api/problems/v1'

/** Envoltura de las listas paginadas del contrato. */
export interface Paginado<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function listarProblemas(
  filtros: { estado?: string; prioridad?: string; origen?: string } = {},
) {
  const query = new URLSearchParams()
  if (filtros.estado) query.set('estado', filtros.estado)
  if (filtros.prioridad) query.set('prioridad', filtros.prioridad)
  if (filtros.origen) query.set('origen', filtros.origen)
  const sufijo = query.toString()
  return apiGet<Paginado<Problema>>(`${BASE}/problemas/${sufijo ? `?${sufijo}` : ''}`)
}

export function listarErroresConocidos(filtros: { activo?: boolean; q?: string } = {}) {
  const query = new URLSearchParams()
  if (filtros.activo !== undefined) query.set('activo', String(filtros.activo))
  if (filtros.q) query.set('q', filtros.q)
  const sufijo = query.toString()
  return apiGet<Paginado<ErrorConocido>>(`${BASE}/errores-conocidos/${sufijo ? `?${sufijo}` : ''}`)
}

export function crearProblema(entrada: ProblemaCrear) {
  return apiPost<Problema>(`${BASE}/problemas/`, entrada)
}

export function cambiarEstadoProblema(id: number, cambio: CambioEstado) {
  return apiPost<Problema>(`${BASE}/problemas/${id}/estado/`, cambio)
}

export function vincularIncidenteProblema(id: number, incidenteId: string) {
  return apiPost<ProblemaIncidente>(`${BASE}/problemas/${id}/incidentes/`, {
    incidente_id: incidenteId,
  })
}

export function crearErrorConocido(entrada: ErrorConocidoCrear) {
  return apiPost<ErrorConocido>(`${BASE}/errores-conocidos/`, entrada)
}
