// Integración del módulo de Eventos con services/events (contracts/events/openapi.yaml).
// Sin datos de ejemplo: si el servicio no responde, la pantalla muestra el error y permite reintentar.
import { ApiError } from '@/api/client'
import { listarEventos, type EventListItem, type EventosFiltros } from '@/api/events'

export async function cargarEventos(filtros: EventosFiltros = {}): Promise<EventListItem[]> {
  const pagina = await listarEventos(filtros)
  // Si el ingress no enruta /api/events, puede llegar otra cosa con 200: se reporta como error.
  if (!Array.isArray(pagina?.results)) {
    throw new ApiError(
      200,
      'El servicio de Eventos respondió en un formato inesperado.',
      'respuesta_invalida',
    )
  }
  return pagina.results
}
