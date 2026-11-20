import { afterEach, describe, expect, it, vi } from 'vitest'
import { listarErroresConocidos, listarProblemas } from './problems'

function json(data: unknown) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

const VACIO = { count: 0, next: null, previous: null, results: [] }

afterEach(() => vi.restoreAllMocks())

describe('api problems', () => {
  it('lista problemas con la ruta del contrato', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarProblemas()
    expect(spy.mock.calls[0][0]).toBe('/api/v1/problemas/')
  })

  it('pasa los filtros como query', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarProblemas({ estado: 'en_analisis', prioridad: 'alta' })
    expect(String(spy.mock.calls[0][0])).toBe('/api/v1/problemas/?estado=en_analisis&prioridad=alta')
  })

  it('lista errores conocidos con filtros', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarErroresConocidos({ activo: true, q: 'SMTP' })
    expect(String(spy.mock.calls[0][0])).toBe('/api/v1/errores-conocidos/?activo=true&q=SMTP')
  })
})
