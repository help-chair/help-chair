import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PublicSite from './PublicSite'

afterEach(() => vi.restoreAllMocks())

describe('PublicSite', () => {
  it('la landing ofrece registrar una empresa', () => {
    render(<PublicSite path="/" />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /registrar mi empresa/i })[0]).toHaveAttribute(
      'href',
      '/registro',
    )
  })

  it('muestra 404 en rutas desconocidas', () => {
    render(<PublicSite path="/nada" />)
    expect(screen.getByText(/página no encontrada/i)).toBeInTheDocument()
  })

  it('informa si el subdominio está disponible', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ disponible: true }), { status: 200 }),
    )
    render(<PublicSite path="/registro" />)
    await userEvent.type(screen.getByLabelText('Subdominio'), 'acme')
    expect(await screen.findByText('Disponible', {}, { timeout: 2000 })).toBeInTheDocument()
  })

  it('rechaza subdominios inválidos sin consultar a la API', async () => {
    const spy = vi.spyOn(globalThis, 'fetch')
    render(<PublicSite path="/registro" />)
    await userEvent.type(screen.getByLabelText('Subdominio'), 'a')
    expect(await screen.findByText(/usa 3 a 30 caracteres/i)).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  it('sin token de seguimiento, la pantalla de estado orienta al usuario', () => {
    render(<PublicSite path="/estado/abc" />)
    expect(screen.getByRole('alert')).toHaveTextContent(/mismo navegador/i)
  })
})
