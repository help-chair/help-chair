import { afterEach, describe, expect, it, vi } from 'vitest'
import { cargarArticulosConRespaldo } from './api'

afterEach(() => vi.restoreAllMocks())

describe('cargarArticulosConRespaldo', () => {
  it('mapea artículos de la API al formato del módulo', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          count: 1,
          next: null,
          previous: null,
          results: [
            {
              id: 'art-1',
              titulo: 'Conectar a la VPN',
              contenido: 'Resumen rápido\nAbrir cliente\nIngresar credenciales',
              categoria: 'red',
              estado: 'publicado',
              visibilidad: 'empresa',
              autor_id: 'usr-1',
              creado_en: '2026-11-23T10:00:00Z',
              actualizado_en: '2026-11-23T10:00:00Z',
              publicado_en: '2026-11-23T10:00:00Z',
              archivado_en: null,
            },
          ],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    const articulos = await cargarArticulosConRespaldo()
    expect(articulos).toHaveLength(1)
    expect(articulos[0].titulo).toBe('Conectar a la VPN')
    expect(articulos[0].visibilidad).toBe('publico')
    expect(articulos[0].pasos).toEqual(['Abrir cliente', 'Ingresar credenciales'])
  })

  it('usa los artículos de ejemplo cuando el servicio no responde', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('sin backend'))
    const articulos = await cargarArticulosConRespaldo()
    expect(articulos.length).toBeGreaterThan(0)
  })
})
