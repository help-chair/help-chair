import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { ApiError, apiGet } from '@/api/client'

// Mock the access module used by the client
vi.mock('@/api/access', () => ({
  refreshSession: vi.fn(() => Promise.resolve({ acceso: 'new-token', refresco: 'new-refresh' })),
  setAccessToken: vi.fn(),
  setRefreshToken: vi.fn(),
  getRefreshToken: vi.fn(() => 'stored-refresh'),
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
