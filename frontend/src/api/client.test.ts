import { ApiError, apiGet } from './client'

afterEach(() => vi.restoreAllMocks())

describe('apiGet', () => {
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
