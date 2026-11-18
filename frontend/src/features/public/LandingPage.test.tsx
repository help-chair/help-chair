import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PublicSite from './PublicSite'

function mockAvailability(disponible: boolean, motivo?: string) {
  return vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue(new Response(JSON.stringify({ disponible, motivo }), { status: 200 }))
}

afterEach(() => {
  vi.restoreAllMocks()
  window.history.pushState({}, '', '/')
})

describe('Página principal', () => {
  it('presenta qué hacemos, cómo funciona y quiénes somos', () => {
    render(<PublicSite path="/" />)

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/propio subdominio/i)
    expect(screen.getByRole('heading', { name: /todo tu service desk/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /cuatro pasos/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /estudiantes del cetI/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Qué hacemos' })).toHaveAttribute(
      'href',
      '#que-hacemos',
    )
  })

  it('ofrece entrar a una empresa existente', () => {
    render(<PublicSite path="/" />)
    for (const link of screen.getAllByRole('link', { name: /entrar a mi empresa/i })) {
      expect(link).toHaveAttribute('href', '/entrar')
    }
  })

  it('comprueba el subdominio y lleva al registro con él', async () => {
    mockAvailability(true)
    const user = userEvent.setup()
    render(<PublicSite path="/" />)

    await user.type(screen.getByLabelText(/elige el subdominio/i), 'Acme Corp')
    expect(screen.getByLabelText(/elige el subdominio/i)).toHaveValue('acmecorp')
    expect(await screen.findByText('Disponible', {}, { timeout: 2000 })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /comenzar registro/i }))
    expect(window.location.pathname).toBe('/registro')
    expect(window.location.search).toBe('?subdominio=acmecorp')
  })

  it('no avanza si el subdominio ya está ocupado', async () => {
    mockAvailability(false, 'ocupado')
    const user = userEvent.setup()
    render(<PublicSite path="/" />)

    await user.type(screen.getByLabelText(/elige el subdominio/i), 'acme')
    expect(await screen.findByText(/ya está en uso/i, {}, { timeout: 2000 })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /comenzar registro/i })).toBeDisabled()
    expect(window.location.pathname).toBe('/')
  })

  it('el registro llega con el subdominio elegido en la landing', () => {
    mockAvailability(true)
    window.history.pushState({}, '', '/registro?subdominio=acme')
    render(<PublicSite path="/registro" />)
    expect(screen.getByLabelText('Subdominio')).toHaveValue('acme')
  })
})
