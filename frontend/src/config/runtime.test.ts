import { loadRuntimeConfig, getRuntimeConfig, resolveHost } from './runtime'

describe('resolveHost', () => {
  it('el dominio base y www son el sitio público', () => {
    expect(resolveHost('help-chair.com', 'help-chair.com', 'desk')).toEqual({
      mode: 'public',
      tenant: null,
    })
    expect(resolveHost('www.help-chair.com', 'help-chair.com', 'desk').mode).toBe('public')
  })

  it('un subdominio de empresa es el Service Desk de ese tenant', () => {
    expect(resolveHost('empresa15.help-chair.com', 'help-chair.com', 'public')).toEqual({
      mode: 'desk',
      tenant: 'empresa15',
    })
  })

  it('los subdominios reservados y anidados no son una empresa', () => {
    expect(resolveHost('api.help-chair.com', 'help-chair.com', 'desk').mode).toBe('public')
    expect(resolveHost('a.b.help-chair.com', 'help-chair.com', 'desk').mode).toBe('public')
  })

  it('un host desconocido usa el valor de respaldo', () => {
    expect(resolveHost('localhost', 'help-chair.com', 'desk').mode).toBe('desk')
    expect(resolveHost('otro.com', 'help-chair.com', 'public').mode).toBe('public')
  })

  it('no confunde dominios que solo terminan igual', () => {
    expect(resolveHost('xhelp-chair.com', 'help-chair.com', 'public').tenant).toBeNull()
  })
})

describe('loadRuntimeConfig', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lee BASE_DOMAIN de /config.json', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ BASE_DOMAIN: 'Help-Chair.com' }), { status: 200 }),
    )
    await loadRuntimeConfig()
    expect(getRuntimeConfig().baseDomain).toBe('help-chair.com')
  })

  it('conserva el valor anterior si falla la lectura', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('sin red'))
    await expect(loadRuntimeConfig()).resolves.toEqual({ baseDomain: 'help-chair.com' })
  })
})
