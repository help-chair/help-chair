import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ActivatePage from './ActivatePage'

afterEach(() => {
  vi.restoreAllMocks()
  window.history.pushState({}, '', '/')
})

describe('ActivatePage', () => {
  it('avisa si falta el token', () => {
    render(<ActivatePage />)
    expect(screen.getByRole('alert')).toHaveTextContent(/incompleto/i)
  })

  it('valida que las contraseñas coincidan antes de llamar a la API', async () => {
    window.history.pushState({}, '', '/activar?token=abc')
    const spy = vi.spyOn(globalThis, 'fetch')
    render(<ActivatePage />)
    await userEvent.type(screen.getByLabelText('Contraseña'), 'una-clave-muy-larga-1')
    await userEvent.type(screen.getByLabelText('Repite la contraseña'), 'otra-distinta-123')
    await userEvent.click(screen.getByRole('button', { name: /activar cuenta/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/no coinciden/i)
    expect(spy).not.toHaveBeenCalled()
  })

  it('activa la cuenta con el token del enlace', async () => {
    window.history.pushState({}, '', '/activar?token=abc')
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }))
    render(<ActivatePage />)
    await userEvent.type(screen.getByLabelText('Contraseña'), 'una-clave-muy-larga-1')
    await userEvent.type(screen.getByLabelText('Repite la contraseña'), 'una-clave-muy-larga-1')
    await userEvent.click(screen.getByRole('button', { name: /activar cuenta/i }))
    expect(await screen.findByText(/ya puedes iniciar sesión/i)).toBeInTheDocument()
    expect(JSON.parse(spy.mock.calls[0][1]?.body as string)).toEqual({
      token: 'abc',
      password: 'una-clave-muy-larga-1',
    })
  })
})
