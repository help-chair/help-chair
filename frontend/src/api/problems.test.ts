import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cambiarEstadoProblema,
  crearErrorConocido,
  crearProblema,
  desvincularIncidenteProblema,
  listarErroresConocidos,
  listarIncidentesDeProblema,
  listarProblemas,
  vincularIncidenteProblema,
} from './problems'

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
    expect(spy.mock.calls[0][0]).toBe('/api/problems/v1/problemas/')
  })

  it('pasa los filtros como query', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarProblemas({ estado: 'en_analisis', prioridad: 'alta' })
    expect(String(spy.mock.calls[0][0])).toBe('/api/problems/v1/problemas/?estado=en_analisis&prioridad=alta')
  })

  it('lista errores conocidos con filtros', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(VACIO))
    await listarErroresConocidos({ activo: true, q: 'SMTP' })
    expect(String(spy.mock.calls[0][0])).toBe('/api/problems/v1/errores-conocidos/?activo=true&q=SMTP')
  })

  it('envía creación, cambio de estado, vínculo y error conocido al contrato v1', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(() => Promise.resolve(json({ id: 42 })))

    await crearProblema({ titulo: 'Caída SMTP', descripcion: 'Falla los lunes' })
    expect(spy.mock.calls[0][0]).toBe('/api/problems/v1/problemas/')
    expect(spy.mock.calls[0][1]?.method).toBe('POST')

    await cambiarEstadoProblema(42, { estado: 'en_analisis' })
    expect(spy.mock.calls[1][0]).toBe('/api/problems/v1/problemas/42/estado/')

    await vincularIncidenteProblema(42, 'INC-1')
    expect(spy.mock.calls[2][0]).toBe('/api/problems/v1/problemas/42/incidentes/')

    await crearErrorConocido({
      problema_id: 42,
      titulo: 'Certificado vencido',
      descripcion: 'Rechaza TLS',
      causa_raiz: 'No se renueva',
      workaround: 'Renovar manualmente',
    })
    expect(spy.mock.calls[3][0]).toBe('/api/problems/v1/errores-conocidos/')
  })

  it('lista y desvincula los incidentes de un problema', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(json([]))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))

    await listarIncidentesDeProblema(42)
    expect(spy.mock.calls[0][0]).toBe('/api/problems/v1/problemas/42/incidentes/')

    await desvincularIncidenteProblema(42, 'INC-000001')
    expect(spy.mock.calls[1][0]).toBe('/api/problems/v1/problemas/42/incidentes/INC-000001/')
    expect(spy.mock.calls[1][1]?.method).toBe('DELETE')
  })
})
