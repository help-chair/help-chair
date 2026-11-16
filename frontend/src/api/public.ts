// API pública de registro de empresas. Contrato: contracts/gateway/openapi.yaml (Plataforma).
import { apiGet, apiPost } from './client'

export type Estado = 'pendiente_verificacion' | 'aprovisionando' | 'activa' | 'suspendida' | 'error'
export type Tamano = '1-10' | '11-50' | '51-200' | '201-1000' | '1000+'

export interface AltaEmpresa {
  empresa: { nombre: string; subdominio: string; sector?: string; tamano?: Tamano; pais?: string }
  administrador: { nombre: string; correo: string }
  acepta_terminos: true
}

export interface SolicitudCreada {
  id: string
  subdominio: string
  estado: Estado
  token_seguimiento: string
}

export interface EstadoEmpresa {
  id: string
  subdominio: string
  estado: Estado
  url?: string | null
  mensaje?: string | null
  enlace_activacion?: string | null
}

export interface Disponibilidad {
  disponible: boolean
  motivo?: 'ocupado' | 'reservado' | 'invalido'
}

const BASE = '/api/public/v1'

export const SUBDOMINIO_REGEX = /^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$/

export function checkSubdomain(subdominio: string, signal?: AbortSignal) {
  return apiGet<Disponibilidad>(
    `${BASE}/subdomains/${encodeURIComponent(subdominio)}/availability`,
    {
      signal,
    },
  )
}

export function registerCompany(data: AltaEmpresa) {
  return apiPost<SolicitudCreada>(`${BASE}/companies`, data)
}

export function verifyCompany(token: string) {
  return apiPost<EstadoEmpresa>(`${BASE}/companies/verify`, { token })
}

export function getCompanyStatus(id: string, trackingToken: string) {
  return apiGet<EstadoEmpresa>(`${BASE}/companies/${encodeURIComponent(id)}/status`, {
    headers: { 'X-Tracking-Token': trackingToken },
  })
}

export function lookupCompany(correo: string) {
  return apiPost<{ subdominio: string; url: string }>(`${BASE}/lookup`, { correo })
}
