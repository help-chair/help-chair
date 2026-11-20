import type { TabKey } from '@/components/layout/ServiceDeskLayout'
import type { Permiso } from './types'

/**
 * Navegación según rol (entregable de la fase 2).
 * Accesos es dueño de los roles, así que aquí se decide qué secciones ve cada quien.
 * `null` = visible para cualquier persona con sesión.
 */
const PERMISO_POR_SECCION: Record<TabKey, Permiso | null> = {
  dashboard: null,
  requests: null,
  knowledge: null,
  events: 'tickets:atender',
  incidents: 'tickets:atender',
  problems: 'tickets:escalar',
  access: 'usuarios:administrar',
}

/** Secciones del menú lateral que corresponden a los permisos de la sesión. */
export function seccionesVisibles(permisos: Permiso[]): TabKey[] {
  return (Object.keys(PERMISO_POR_SECCION) as TabKey[]).filter((seccion) => {
    const requerido = PERMISO_POR_SECCION[seccion]
    return requerido === null || permisos.includes(requerido)
  })
}

/** Evita quedarse en una sección que el rol no puede ver (p. ej. al cambiar de usuario). */
export function seccionInicial(permisos: Permiso[]): TabKey {
  return seccionesVisibles(permisos).includes('dashboard') ? 'dashboard' : 'requests'
}
