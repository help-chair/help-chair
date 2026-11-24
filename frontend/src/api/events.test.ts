import { afterEach, describe, expect, it, vi } from 'vitest'
import { listarEventos } from './events'

function json(data: unknown) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

const VACIO = { count: 0, next: null, previous: null, results: [] }

afterEach(() => vi.restoreAllMocks())

describe('api events', () => {
  it('lista eventos con la ruta del contrato', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarEventos()
    expect(spy.mock.calls[0][0]).toBe('/api/events/v1/events')
  })

  it('pasa los filtros como query', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarEventos({ state: 'NEW', event_type: 'EXCEPTION', open: true })
    expect(String(spy.mock.calls[0][0])).toBe('/api/events/v1/events?state=NEW&event_type=EXCEPTION&open=true')
  })
})
