// API de Problemas. Contrato: contracts/problems/openapi.yaml (Equipo 5).
// OJO: el contrato declara `servers.url = http://localhost:8005/api/v1`, así que las rutas
// completas son `/api/v1/problemas/` y `/api/v1/errores-conocidos/`. El proxy de Vite hoy mapea
// `/api/problems` (no `/api/v1`); reconciliar la base antes de conectar el módulo a Prism (issue #146).
import { apiGet } from './client'
import type { ErrorConocido, Problema } from '@/features/problems/types'

const BASE = '/api/v1'

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
