import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { CLAVE_DEMO } from '@/features/access/data'
import type { Sesion } from '@/features/access/types'

const sesion: Sesion = {
  acceso: 'jwt-de-prueba',
  refresco: 'refresco-de-prueba',
  token_tipo: 'Bearer',
  expira_en: 900,
  usuario: {
    id: 'usr-1',
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

/** Deja la aplicación con sesión iniciada. */
async function entrar() {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/correo de trabajo/i), 'admin@acme.com')
  await user.type(screen.getByLabelText(/^contraseña/i), 'una-clave-muy-larga-1')
  await user.click(screen.getByRole('button', { name: /entrar/i }))
  return user
}

describe('App', () => {
  it('muestra el título del producto', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /help chair/i })).toBeInTheDocument()
  })

  it('pide iniciar sesión antes de mostrar el Service Desk', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /inicia sesión/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /dashboard principal/i })).not.toBeInTheDocument()
  })

  it('entra al Service Desk con el usuario de la sesión', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(sesion))
    render(<App />)
    await entrar()

    expect(await screen.findByRole('button', { name: /dashboard principal/i })).toBeInTheDocument()
    expect(screen.getByText('Admin Help Desk')).toBeInTheDocument()
    expect(screen.getByText('Administrador')).toBeInTheDocument()
  })

  it('abre el módulo de Accesos y permite cerrar sesión', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input)
      if (url.startsWith('/api/access/v1/login')) return Promise.resolve(json(sesion))
      if (url.startsWith('/api/access/v1/roles')) return Promise.resolve(json({ resultados: [] }))
      return Promise.resolve(json({ resultados: [] }))
    })
    render(<App />)
    const user = await entrar()

    await user.click(await screen.findByRole('button', { name: 'Accesos' }))
    expect(screen.getByRole('heading', { name: /gestión de accesos \(access management\)/i }))
      .toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /salir/i }))
    expect(screen.getByRole('heading', { name: /inicia sesión/i })).toBeInTheDocument()
  })

  it('oculta del menú las secciones que el rol no puede ver', async () => {
    // Sin microservicio, el login cae en los datos simulados: Lucía es usuario final.
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    render(<App />)

    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/correo de trabajo/i), 'lucia.ponce@empresa15.com')
    await user.type(screen.getByLabelText(/^contraseña/i), CLAVE_DEMO)
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    const menu = within(await screen.findByRole('navigation', { name: /secciones/i }))
    expect(menu.getByRole('button', { name: /peticiones/i })).toBeInTheDocument()
    expect(menu.getByRole('button', { name: /base de conocimiento/i })).toBeInTheDocument()
    expect(menu.queryByRole('button', { name: 'Accesos' })).not.toBeInTheDocument()
    expect(menu.queryByRole('button', { name: /problemas/i })).not.toBeInTheDocument()
    expect(menu.queryByRole('button', { name: /gestión de eventos/i })).not.toBeInTheDocument()
  })

  it('permite al administrador acceder a la sección de peticiones', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input)
      if (url.startsWith('/api/access/v1/login')) return Promise.resolve(json(sesion))
      return Promise.resolve(json({ resultados: [] }))
    })
    render(<App />)
    const user = await entrar()

    const menu = within(await screen.findByRole('navigation', { name: /secciones/i }))
    await user.click(menu.getByRole('button', { name: /peticiones/i }))
    expect(screen.queryByText(/no tienes permiso para ver solicitudes/i)).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /gestión de peticiones/i })).toBeInTheDocument()
  })

  async function entrarSimulado(correo: string) {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    render(<App />)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/correo de trabajo/i), correo)
    await user.type(screen.getByLabelText(/^contraseña/i), CLAVE_DEMO)
    await user.click(screen.getByRole('button', { name: /entrar/i }))
    return user
  }

  it('agente N1 ve Eventos e Incidencias, pero no Problemas ni Accesos', async () => {
    await entrarSimulado('daniela.ruiz@empresa15.com')
    const menu = within(await screen.findByRole('navigation', { name: /secciones/i }))

    expect(menu.getByRole('button', { name: /gestión de eventos/i })).toBeInTheDocument()
    expect(menu.getByRole('button', { name: /incidencias/i })).toBeInTheDocument()
    expect(menu.queryByRole('button', { name: /problemas/i })).not.toBeInTheDocument()
    expect(menu.queryByRole('button', { name: 'Accesos' })).not.toBeInTheDocument()
  })

  it('agente N2 ve Problemas y su panel de área en el dashboard, no Accesos', async () => {
    await entrarSimulado('marco.estrada@empresa15.com')
    const menu = within(await screen.findByRole('navigation', { name: /secciones/i }))

    expect(menu.getByRole('button', { name: /problemas/i })).toBeInTheDocument()
    expect(menu.queryByRole('button', { name: 'Accesos' })).not.toBeInTheDocument()
    expect(
      await screen.findByRole('heading', { name: /panel de área operativa/i }),
    ).toBeInTheDocument()
  })

  it('agente N2 abre Incidencias y ve la gestión, no el panel estático', async () => {
    const user = await entrarSimulado('marco.estrada@empresa15.com')
    const menu = within(await screen.findByRole('navigation', { name: /secciones/i }))

    await user.click(menu.getByRole('button', { name: /incidencias/i }))

    expect(await screen.findByRole('heading', { name: /gestión de incidentes/i })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /panel de área operativa/i })).not.toBeInTheDocument()
  })
})
