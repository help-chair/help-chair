import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UsersPage } from './UsersPage'
import type { Rol, Usuario, UsuarioActual } from './types'

const roles: Rol[] = [
  {
    id: 'administrador',
    nombre: 'Administrador',
    descripcion: 'Configura la empresa y administra usuarios.',
    permisos: ['tickets:ver', 'empresa:configurar', 'usuarios:administrar'],
  },
  { id: 'agente_n2', nombre: 'Agente N2', permisos: ['tickets:ver', 'tickets:escalar'] },
  { id: 'agente_n1', nombre: 'Agente N1', permisos: ['tickets:ver', 'tickets:atender'] },
  { id: 'usuario_final', nombre: 'Usuario final', permisos: ['tickets:ver'] },
]

const admin: UsuarioActual = {
  id: 'usr-1',
  nombre: 'Admin Help Desk',
  correo: 'admin@acme.com',
  rol: 'administrador',
  estado: 'activo',
  permisos: ['tickets:ver', 'empresa:configurar', 'usuarios:administrar'],
  onboarding_completed: true,
}

const usuarioFinal: UsuarioActual = {
  ...admin,
  id: 'usr-9',
  nombre: 'Lucía Ponce',
  correo: 'lucia@acme.com',
  rol: 'usuario_final',
  permisos: ['tickets:ver'],
}

const daniela: Usuario = {
  id: 'usr-2',
  nombre: 'Daniela Ruiz',
  correo: 'daniela@acme.com',
  rol: 'agente_n1',
  departamento: 'Sistemas',
  estado: 'activo',
  ultimo_acceso: '2026-11-16T15:40:00.000Z',
}

const hugo: Usuario = {
  id: 'usr-3',
  nombre: 'Hugo Navarro',
  correo: 'hugo@acme.com',
  rol: 'usuario_final',
  departamento: 'Ventas',
  estado: 'bloqueado',
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Responde a cada ruta de Accesos; `extra` sobrescribe rutas concretas en una prueba. */
function mockAccesos(
  usuarios: Usuario[] = [daniela, hugo],
  extra: (url: string, init?: RequestInit) => Response | null = () => null,
) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
    const url = String(input)
    const personalizada = extra(url, init)
    if (personalizada) return Promise.resolve(personalizada)
    if (url.startsWith('/api/access/v1/roles')) return Promise.resolve(json({ resultados: roles }))
    if (url.startsWith('/api/access/v1/usuarios'))
      return Promise.resolve(json({ resultados: usuarios }))
    return Promise.resolve(json({ codigo: 'no_encontrado', detalle: url }, 404))
  })
}

afterEach(() => vi.restoreAllMocks())

describe('UsersPage', () => {
  it('lista los usuarios que devuelve Accesos', async () => {
    mockAccesos()
    render(<UsersPage usuario={admin} />)

    expect(await screen.findByText('Daniela Ruiz')).toBeInTheDocument()
    expect(screen.getByText('hugo@acme.com')).toBeInTheDocument()
    expect(screen.getByText('Bloqueada')).toBeInTheDocument()
  })

  it('oculta las acciones a quien no tiene usuarios:administrar', async () => {
    mockAccesos()
    render(<UsersPage usuario={usuarioFinal} />)

    expect(await screen.findByText('Daniela Ruiz')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /invitar/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/rol de daniela ruiz/i)).not.toBeInTheDocument()
  })

  it('invita a un usuario y lo agrega a la lista', async () => {
    const nuevo: Usuario = {
      id: 'usr-4',
      nombre: 'Marco Estrada',
      correo: 'marco@acme.com',
      rol: 'agente_n2',
      estado: 'invitado',
    }
    const spy = mockAccesos([daniela, hugo], (url, init) =>
      url === '/api/access/v1/usuarios' && init?.method === 'POST' ? json(nuevo, 201) : null,
    )
    render(<UsersPage usuario={admin} />)
    await screen.findByText('Daniela Ruiz')

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('Nombre'), 'Marco Estrada')
    await user.type(screen.getByLabelText('Correo'), 'marco@acme.com')
    const selectorRol = screen.getByLabelText('Rol', { selector: '#invitar-rol' })
    await user.selectOptions(selectorRol, 'agente_n2')
    await user.click(screen.getByRole('button', { name: /invitar/i }))

    expect(await screen.findByRole('status')).toHaveTextContent('marco@acme.com')
    expect(screen.getByText('Marco Estrada')).toBeInTheDocument()

    const envio = spy.mock.calls.find(
      ([url, init]) => url === '/api/access/v1/usuarios' && init?.method === 'POST',
    )
    expect(JSON.parse(envio?.[1]?.body as string)).toEqual({
      nombre: 'Marco Estrada',
      correo: 'marco@acme.com',
      rol: 'agente_n2',
    })
  })

  it('cambia el rol de un usuario con PATCH', async () => {
    const spy = mockAccesos([daniela], (url, init) =>
      url === '/api/access/v1/usuarios/usr-2' && init?.method === 'PATCH'
        ? json({ ...daniela, rol: 'agente_n2' })
        : null,
    )
    render(<UsersPage usuario={admin} />)

    const user = userEvent.setup()
    await user.selectOptions(await screen.findByLabelText(/rol de daniela ruiz/i), 'agente_n2')

    expect(await screen.findByRole('status')).toHaveTextContent(/daniela ruiz ahora es agente n2/i)
    const envio = spy.mock.calls.find(([, init]) => init?.method === 'PATCH')
    expect(JSON.parse(envio?.[1]?.body as string)).toEqual({ rol: 'agente_n2' })
  })

  it('desbloquea una cuenta bloqueada por intentos fallidos', async () => {
    mockAccesos([hugo], (url, init) =>
      url === '/api/access/v1/usuarios/usr-3/desbloquear' && init?.method === 'POST'
        ? json({ ...hugo, estado: 'activo' })
        : null,
    )
    render(<UsersPage usuario={admin} />)

    await userEvent.click(await screen.findByRole('button', { name: /desbloquear/i }))

    expect(await screen.findByRole('status')).toHaveTextContent(/reactivada/i)
    const fila = screen.getByText('Hugo Navarro').closest('tr')!
    expect(within(fila).getByText('Activa')).toBeInTheDocument()
  })

  it('sin conexión con Accesos muestra el error, sin datos simulados', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    render(<UsersPage usuario={admin} />)

    expect(await screen.findByRole('alert')).toHaveTextContent(/no hay conexión con el servicio/i)
    expect(screen.queryByText('Admin Help Desk')).not.toBeInTheDocument()
  })

  it('propaga un 403 del microservicio', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      json({ codigo: 'permiso_denegado', detalle: 'Sin permiso' }, 403),
    )
    render(<UsersPage usuario={admin} />)

    expect(await screen.findByRole('alert')).toHaveTextContent(/no puede consultar/i)
  })
})
