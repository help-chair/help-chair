import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  ApiError,
  TIEMPO_LIMITE_MS,
  apiDelete,
  apiGet,
  apiPatch,
  esErrorDeConexion,
} from '@/api/client'

// Mock the access module used by the client
vi.mock('@/api/access', () => ({
  refreshSession: vi.fn(() => Promise.resolve({ acceso: 'new-token', refresco: 'new-refresh' })),
  setAccessToken: vi.fn(),
  setRefreshToken: vi.fn(),
  getRefreshToken: vi.fn(() => 'stored-refresh'),
  getAccessToken: vi.fn(() => 'token-vigente'),
}))

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('devuelve el JSON cuando la respuesta es 200', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), { status: 200 }),
    )
    await expect(apiGet('/health/live')).resolves.toEqual({ status: 'ok' })
  })

  it('lanza ApiError cuando la respuesta no es exitosa', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 503 }))
    await expect(apiGet('/health/ready')).rejects.toBeInstanceOf(ApiError)
  })
})

describe('api client JWT refresh', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('retries once after a 401 and returns data', async () => {
    let callCount = 0

    // @ts-expect-error -- intentional global.fetch mock for test
    global.fetch = vi.fn(() => {
      callCount++
      if (callCount === 1) {
        return Promise.resolve({ ok: false, status: 401, json: () => ({}) })
      }
      return Promise.resolve({ ok: true, status: 200, json: () => ({ data: 123 }) })
    })

    const result = await apiGet<{ data: number }>('/test')

    expect(result).toEqual({ data: 123 })

    const { refreshSession, setAccessToken, setRefreshToken } = await import('@/api/access')
    expect(refreshSession).toHaveBeenCalledWith('stored-refresh')
    expect(setAccessToken).toHaveBeenCalledWith('new-token')
    expect(setRefreshToken).toHaveBeenCalledWith('new-refresh')
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('throws after a failed refresh', async () => {
    // @ts-expect-error -- intentional global.fetch mock for test
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 401, json: () => ({}) }),
    )

    const access = await import('@/api/access')
    vi.mocked(access.refreshSession).mockRejectedValueOnce(new Error('refresh fail'))

    await expect(apiGet('/test')).rejects.toThrow()

    expect(access.setAccessToken).toHaveBeenCalledWith(null)
    expect(access.setRefreshToken).toHaveBeenCalledWith(null)
  })

  it('no intenta refrescar si no hay token de refresco guardado', async () => {
    // @ts-expect-error -- intentional global.fetch mock for test
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 401, json: () => ({}) }),
    )

    const access = await import('@/api/access')
    vi.mocked(access.getRefreshToken).mockReturnValue(null)
    vi.mocked(access.refreshSession).mockClear()

    await expect(apiGet('/test')).rejects.toThrow()

    expect(access.refreshSession).not.toHaveBeenCalled()
    expect(access.setAccessToken).toHaveBeenCalledWith(null)
    expect(access.setRefreshToken).toHaveBeenCalledWith(null)
  })

  it('does not attempt refresh for login endpoint', async () => {
    // @ts-expect-error -- intentional global.fetch mock for test
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 401, json: () => ({ codigo: 'credenciales_invalidas' }) }),
    )

    const access = await import('@/api/access')
    vi.mocked(access.refreshSession).mockClear()

    await expect(apiGet('/api/access/v1/login')).rejects.toThrow()
    expect(access.refreshSession).not.toHaveBeenCalled()
  })
})

describe('api client: red, tiempos y formatos de error', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('agrega el JWT en las llamadas del Service Desk', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify({}), { status: 200 }))
    await apiGet('/api/incidents/v1/incidents/')
    const headers = spy.mock.calls[0][1]?.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer token-vigente')
  })

  it('no envía el JWT a la API pública', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify({}), { status: 200 }))
    await apiGet('/api/public/v1/subdomains/acme/availability')
    const headers = spy.mock.calls[0][1]?.headers as Record<string, string>
    expect(headers.Authorization).toBeUndefined()
  })

  it('convierte un fallo de red en ApiError con status 0', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    const error = await apiGet('/api/events/v1/events').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).code).toBe('sin_conexion')
    expect(esErrorDeConexion(error)).toBe(true)
  })

  it('corta la petición al agotarse el tiempo de espera', async () => {
    vi.useFakeTimers()
    vi.spyOn(globalThis, 'fetch').mockImplementation(
      (_input, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          )
        }),
    )
    const promesa = apiGet('/api/problems/v1/problemas/').catch((e: unknown) => e)
    await vi.advanceTimersByTimeAsync(TIEMPO_LIMITE_MS)
    const error = await promesa
    expect((error as ApiError).status).toBe(0)
    expect((error as ApiError).code).toBe('tiempo_agotado')
  })

  it('respeta la cancelación de quien llama (AbortError)', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(
      (_input, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          )
        }),
    )
    const controlador = new AbortController()
    const promesa = apiGet('/api/public/v1/lookup', { signal: controlador.signal }).catch(
      (e: unknown) => e,
    )
    controlador.abort()
    const error = await promesa
    expect(error).not.toBeInstanceOf(ApiError)
    expect((error as DOMException).name).toBe('AbortError')
  })

  it('toma el mensaje de los errores de campo de Django REST Framework', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: ['No se puede pasar de «nuevo» a «cerrado».'] }), {
        status: 400,
      }),
    )
    const error = (await apiPatch('/api/incidents/v1/incidents/1/', { status: 'cerrado' }).catch(
      (e: unknown) => e,
    )) as ApiError
    expect(error.status).toBe(400)
    expect(error.message).toBe('No se puede pasar de «nuevo» a «cerrado».')
    expect(error.fields).toEqual({ status: 'No se puede pasar de «nuevo» a «cerrado».' })
  })

  it('reporta una respuesta que no es JSON (p. ej. el index.html del SPA)', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('<!doctype html><html></html>', { status: 200 }),
    )
    const error = (await apiGet('/api/requests/v1/peticiones/').catch(
      (e: unknown) => e,
    )) as ApiError
    expect(error.code).toBe('respuesta_invalida')
  })

  it('DELETE acepta 204 sin cuerpo', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }))
    await expect(apiDelete('/api/problems/v1/problemas/1/incidentes/INC-1/')).resolves.toBeUndefined()
    expect(spy.mock.calls[0][1]?.method).toBe('DELETE')
  })
})
