import { afterEach, describe, expect, it, vi } from 'vitest'
import { listarIncidentes } from './incidents'

function json(data: unknown) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

const VACIO = { count: 0, next: null, previous: null, results: [] }

afterEach(() => vi.restoreAllMocks())

describe('api incidents', () => {
  it('lista incidentes con la ruta del contrato', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarIncidentes()
    expect(spy.mock.calls[0][0]).toBe('/api/incidents/v1/incidents/')
  })

  it('pasa los filtros como query', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarIncidentes({ status: 'asignado', priority: 'P1' })
    expect(String(spy.mock.calls[0][0])).toBe('/api/incidents/v1/incidents/?status=asignado&priority=P1')
  })
})
