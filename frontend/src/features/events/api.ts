// Integración del módulo de Eventos con services/events.
// Llama a la API real y, si el servicio no responde, usa datos de ejemplo.
import { ApiError } from '@/api/client'
import { listarEventos, type EventListItem } from '@/api/events'

function servicioInalcanzable(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 404 || error.status >= 500
  return true
}

const EVENTOS_DE_EJEMPLO: EventListItem[] = [
  {
    id: '7c9e6679-7425-40de-944b-e07fc1f90ae7',
    origin: 'SYSTEM',
    event_type: 'EXCEPTION',
    category: 'FAILURE',
    title: 'Timeout en el gateway de pagos',
    priority: 'P1',
    state: 'NEW',
    service_code: 'pagos',
    destination: 'INCIDENTS',
    assigned_to_ref: null,
    occurrence_count: 1,
    last_seen_at: '2026-11-22T11:15:00Z',
    resolution_due_at: '2026-11-22T13:15:00Z',
    created_at: '2026-11-22T11:15:00Z',
  },
  {
    id: '5f4d2a10-9c3b-4e6d-8a1f-2b0c7d9e4a01',
    origin: 'SYSTEM',
    event_type: 'WARNING',
    category: 'GENERAL',
    title: 'Espacio en disco superior al 85 % en bd-cluster-02',
    priority: 'P2',
    state: 'ASSIGNED',
    service_code: 'base-datos',
    destination: 'EVENTS',
    assigned_to_ref: 'usr-002',
    occurrence_count: 3,
    last_seen_at: '2026-11-22T11:10:00Z',
    resolution_due_at: null,
    created_at: '2026-11-22T10:55:00Z',
  },
  {
    id: 'a1b2c3d4-5566-7788-99aa-bbccddeeff01',
    origin: 'USER',
    event_type: 'INFORMATION',
    category: 'REQUEST',
    title: 'Solicitud de acceso a VPN para nuevo colaborador',
    priority: 'P4',
    state: 'RESOLVED',
    service_code: 'vpn',
    destination: 'REQUESTS',
    assigned_to_ref: null,
    occurrence_count: 1,
    last_seen_at: '2026-11-22T10:30:00Z',
    resolution_due_at: null,
    created_at: '2026-11-22T10:30:00Z',
  },
  {
    id: 'd9e8f7a6-4433-2211-00ff-9e8d7c6b5a04',
    origin: 'SYSTEM',
    event_type: 'EXCEPTION',
    category: 'SECURITY',
    title: 'Intentos fallidos de autenticación reiterados',
    priority: 'P1',
    state: 'IN_PROGRESS',
    service_code: 'accesos',
    destination: 'ACCESS',
    assigned_to_ref: 'usr-006',
    occurrence_count: 5,
    last_seen_at: '2026-11-22T09:50:00Z',
    resolution_due_at: '2026-11-22T10:20:00Z',
    created_at: '2026-11-22T09:48:00Z',
  },
]

export async function cargarEventosConRespaldo(): Promise<EventListItem[]> {
  try {
    const pagina = await listarEventos()
    return pagina.results
  } catch (error) {
    if (!servicioInalcanzable(error)) throw error
    return EVENTOS_DE_EJEMPLO
  }
}
