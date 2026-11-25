import { afterEach, describe, expect, it, vi } from 'vitest'
import { actualizarIncidente, crearIncidente, listarIncidentes } from './incidents'

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

  it('crea y actualiza un incidente contra el contrato v1', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(() => Promise.resolve(json({ id: 7 })))
    await crearIncidente({
      title: 'Sin red',
      description: 'Sin acceso en edificio B',
      impact: 'alto',
      urgency: 'alta',
      reported_by: 'usr-001',
    })
    expect(spy.mock.calls[0][0]).toBe('/api/incidents/v1/incidents/')
    expect(spy.mock.calls[0][1]?.method).toBe('POST')

    await actualizarIncidente(7, { status: 'asignado', assigned_to: 'usr-002' })
    expect(spy.mock.calls[1][0]).toBe('/api/incidents/v1/incidents/7/')
    expect(spy.mock.calls[1][1]?.method).toBe('PATCH')
  })
})
