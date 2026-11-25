// Catálogos y utilidades del módulo de Eventos (contracts/events/openapi.yaml).
// Los eventos vienen siempre de services/events: aquí no hay datos de ejemplo.
import type { BadgeProps } from '@/components/ui/badge'
import type { Destination, EventState, EventType } from './types'

export const TIPO_BADGE: Record<EventType, NonNullable<BadgeProps['variant']>> = {
  INFORMATION: 'info',
  WARNING: 'warning',
  EXCEPTION: 'exception',
}

export const TIPO_LABEL: Record<EventType, string> = {
  INFORMATION: 'Informativo',
  WARNING: 'Advertencia',
  EXCEPTION: 'Excepción',
}

export const DESTINO_LABEL: Record<Destination, string> = {
  LOG_ONLY: 'Solo registro',
  SOLUTION_AUTHOR: 'Autor de la solución (KB)',
  EVENTS: 'Registro y vigilancia',
  ACCESS: 'Accesos / Seguridad',
  REQUESTS: 'Peticiones',
  INCIDENTS: 'Incidencias',
  PROBLEMS: 'Problemas',
}

export const ESTADO_LABEL: Record<EventState, string> = {
  NEW: 'Nuevo',
  ASSIGNED: 'Asignado',
  IN_PROGRESS: 'En proceso',
  ON_HOLD: 'En espera',
  RESOLVED: 'Resuelto',
  CLOSED: 'Cerrado',
  REJECTED: 'Rechazado',
  CANCELLED: 'Cancelado',
  REOPENED: 'Reabierto',
}

/** «11:15» */
export function hora(iso: string) {
  return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })
}
