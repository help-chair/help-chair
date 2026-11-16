import { ApiError } from './client'
import { checkSubdomain, getCompanyStatus, registerCompany, verifyCompany } from './public'

afterEach(() => vi.restoreAllMocks())

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })

describe('API pública de registro', () => {
  it('consulta la disponibilidad con ruta relativa', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json({ disponible: true }))
    await expect(checkSubdomain('empresa15')).resolves.toEqual({ disponible: true })
    expect(spy.mock.calls[0][0]).toBe('/api/public/v1/subdomains/empresa15/availability')
  })

  it('envía el alta por POST con JSON', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        json(
          { id: 'x', subdominio: 'acme', estado: 'pendiente_verificacion', token_seguimiento: 't' },
          202,
        ),
      )
    await registerCompany({
      empresa: { nombre: 'Acme', subdominio: 'acme' },
      administrador: { nombre: 'Ana', correo: 'ana@acme.com' },
      acepta_terminos: true,
    })
    const [url, init] = spy.mock.calls[0]
    expect(url).toBe('/api/public/v1/companies')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string).administrador.correo).toBe('ana@acme.com')
  })

  it('verifica el correo con POST (no GET)', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(json({ id: 'x', subdominio: 'acme', estado: 'aprovisionando' }))
    await verifyCompany('tok')
    expect(spy.mock.calls[0][1]?.method).toBe('POST')
  })

  it('manda el token de seguimiento en el encabezado', async () => {
    const spy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(json({ id: 'x', subdominio: 'acme', estado: 'activa' }))
    await getCompanyStatus('x', 'seg')
    expect((spy.mock.calls[0][1]?.headers as Record<string, string>)['X-Tracking-Token']).toBe(
      'seg',
    )
  })

  it('traduce el error del contrato a ApiError', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      json({ codigo: 'subdominio_ocupado', detalle: 'Ya existe' }, 409),
    )
    await expect(checkSubdomain('acme')).rejects.toMatchObject({
      status: 409,
      code: 'subdominio_ocupado',
      message: 'Ya existe',
    })
    await expect(checkSubdomain('acme')).rejects.toBeInstanceOf(ApiError)
  })
})
