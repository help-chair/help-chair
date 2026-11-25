import { afterEach, describe, expect, it, vi } from 'vitest'
import { crearArticulo, listarArticulos } from './knowledge'

function json(data: unknown) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

const VACIO = { count: 0, next: null, previous: null, results: [] }

afterEach(() => vi.restoreAllMocks())

describe('api knowledge', () => {
  it('lista artículos con la ruta del contrato', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarArticulos()
    expect(spy.mock.calls[0][0]).toBe('/api/knowledge/v1/articulos/')
  })

  it('pasa los filtros de búsqueda y categoría como query', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarArticulos({ q: 'wifi', categoria: 'red', estado: 'publicado' })
    expect(String(spy.mock.calls[0][0])).toBe(
      '/api/knowledge/v1/articulos/?q=wifi&categoria=red&estado=publicado',
    )
  })

  it('crea un artículo en borrador', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json({ id: 'uuid-1' }))
    await crearArticulo({ titulo: 'Guía VPN', contenido: 'Paso 1', visibilidad: 'empresa' })
    expect(spy.mock.calls[0][0]).toBe('/api/knowledge/v1/articulos/')
    expect(spy.mock.calls[0][1]?.method).toBe('POST')
  })
})
