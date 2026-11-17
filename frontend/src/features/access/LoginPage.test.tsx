import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from './LoginPage'
import type { Sesion } from './types'

const sesion: Sesion = {
  acceso: 'jwt-de-prueba',
  refresco: 'refresco-de-prueba',
  token_tipo: 'Bearer',
  expira_en: 900,
  usuario: {
    id: '11111111-1111-4111-8111-111111111111',
    nombre: 'Admin Help Desk',
    correo: 'admin@acme.com',
    rol: 'administrador',
    estado: 'activo',
    permisos: ['tickets:ver', 'empresa:configurar', 'usuarios:administrar'],
    onboarding_completed: true,
  },
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => vi.restoreAllMocks())

async function capturar(correo: string, password: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/correo de trabajo/i), correo)
  await user.type(screen.getByLabelText(/^contraseña/i), password)
  await user.click(screen.getByRole('button', { name: /entrar/i }))
}

describe('LoginPage', () => {
  it('muestra el host de la empresa', () => {
    render(<LoginPage onAuthenticated={vi.fn()} />)
    expect(screen.getByText(window.location.host)).toBeInTheDocument()
  })

  it('valida los campos antes de llamar a la API', async () => {
    const spy = vi.spyOn(globalThis, 'fetch')
    render(<LoginPage onAuthenticated={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: /entrar/i }))

    expect(screen.getByText('Escribe tu correo de trabajo.')).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  it('entrega la sesión cuando las credenciales son correctas', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(sesion))
    const onAuthenticated = vi.fn()
    render(<LoginPage onAuthenticated={onAuthenticated} />)

    await capturar('admin@acme.com', 'una-clave-muy-larga-1')

    expect(spy.mock.calls[0][0]).toBe('/api/access/v1/login')
    expect(JSON.parse(spy.mock.calls[0][1]?.body as string)).toEqual({
      correo: 'admin@acme.com',
      password: 'una-clave-muy-larga-1',
    })
    expect(onAuthenticated).toHaveBeenCalledWith(sesion)
  })

  it('avisa cuando el correo o la contraseña no coinciden', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      json({ codigo: 'credenciales_invalidas', detalle: 'No coincide' }, 401),
    )
    render(<LoginPage onAuthenticated={vi.fn()} />)

    await capturar('admin@acme.com', 'incorrecta-pero-larga')

    expect(await screen.findByRole('alert')).toHaveTextContent(/incorrectos/i)
    expect(screen.getByRole('button', { name: /entrar/i })).toBeEnabled()
  })

  it('bloquea la captura cuando la cuenta está bloqueada por intentos fallidos', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      json({ codigo: 'cuenta_bloqueada', detalle: 'Cuenta bloqueada por intentos fallidos.' }, 423),
    )
    render(<LoginPage onAuthenticated={vi.fn()} />)

    await capturar('admin@acme.com', 'una-clave-muy-larga-1')

    expect(await screen.findByRole('alert')).toHaveTextContent(/bloqueada/i)
    expect(screen.getByRole('button', { name: /entrar/i })).toBeDisabled()
  })
})
