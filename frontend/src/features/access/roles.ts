import type { RolId } from './types'

/**
 * Nombres para mostrar mientras no se ha cargado el catálogo de GET /api/access/v1/roles.
 * El catálogo de la API manda: esto es solo el respaldo para pintar la primera vista.
 */
export const NOMBRE_ROL: Record<RolId, string> = {
  administrador: 'Administrador',
  agente_n2: 'Agente N2',
  agente_n1: 'Agente N1',
  usuario_final: 'Usuario final',
}
