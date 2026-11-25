// API de Base de Conocimiento. Contrato: contracts/knowledge/openapi.yaml (Equipo 5).
import { apiGet, apiPost } from './client'

const BASE = '/api/knowledge/v1'

export type EstadoArticuloContrato = 'borrador' | 'publicado' | 'archivado'
export type VisibilidadArticuloContrato = 'empresa' | 'soporte'

export interface ArticuloContrato {
  id: string
  titulo: string
  contenido: string
  categoria: string | null
  estado: EstadoArticuloContrato
  visibilidad: VisibilidadArticuloContrato
  autor_id: string | null
  creado_en: string
  actualizado_en: string
  publicado_en: string | null
  archivado_en: string | null
}

export interface PaginaArticulos {
  count: number
  next: string | null
  previous: string | null
  results: ArticuloContrato[]
}

export interface ArticuloCrearInput {
  titulo?: string
  contenido?: string
  categoria?: string | null
  visibilidad?: VisibilidadArticuloContrato
}

export function listarArticulos(
  filtros: { q?: string; categoria?: string; estado?: EstadoArticuloContrato; pagina?: number } = {},
) {
  const query = new URLSearchParams()
  if (filtros.q) query.set('q', filtros.q)
  if (filtros.categoria) query.set('categoria', filtros.categoria)
  if (filtros.estado) query.set('estado', filtros.estado)
  if (filtros.pagina) query.set('pagina', String(filtros.pagina))
  const sufijo = query.toString()
  return apiGet<PaginaArticulos>(`${BASE}/articulos/${sufijo ? `?${sufijo}` : ''}`)
}

export function crearArticulo(entrada: ArticuloCrearInput) {
  return apiPost<ArticuloContrato>(`${BASE}/articulos/`, entrada)
}
