import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { OnboardingWizard } from './OnboardingWizard'
import type { Departamento, Rol, Usuario, UsuarioActual } from './types'

const admin: UsuarioActual = {
  id: 'usr-1',
  nombre: 'Admin Help Desk',
  correo: 'admin@acme.com',
  rol: 'administrador',
  estado: 'activo',
  permisos: ['tickets:ver', 'empresa:configurar', 'usuarios:administrar'],
  onboarding_completed: false,
}

const sistemas: Departamento = { id: 'dep-1', nombre: 'Sistemas' }
const finanzas: Departamento = { id: 'dep-2', nombre: 'Finanzas' }

const roles: Rol[] = [
  { id: 'administrador', nombre: 'Administrador', permisos: ['usuarios:administrar'] },
  { id: 'agente_n1', nombre: 'Agente N1', permisos: ['tickets:atender'] },
  { id: 'usuario_final', nombre: 'Usuario final', permisos: ['tickets:ver'] },
]

const invitado: Usuario = {
  id: 'usr-9',
  nombre: 'Lucía Ponce',
  correo: 'lucia@acme.com',
  rol: 'usuario_final',
  estado: 'invitado',
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Responde a las rutas del contrato de Accesos; `extra` sobrescribe una ruta concreta. */
function mockAccesos(
  departamentos: Departamento[] = [sistemas],
  extra: (url: string, init?: RequestInit) => Response | null = () => null,
) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
    const url = String(input)
    const propia = extra(url, init)
    if (propia) return Promise.resolve(propia)
    if (url.startsWith('/api/access/v1/departamentos')) {
      return Promise.resolve(json({ resultados: departamentos }))
    }
    if (url.startsWith('/api/access/v1/roles')) return Promise.resolve(json({ resultados: roles }))
    return Promise.resolve(json({ codigo: 'no_encontrado', detalle: url }, 404))
  })
}

afterEach(() => vi.restoreAllMocks())

/** Avanza del paso que esté al siguiente. */
async function continuar(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /continuar/i }))
}

describe('OnboardingWizard', () => {
  it('muestra los departamentos que ya tiene la empresa', async () => {
    mockAccesos([sistemas, finanzas])
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)

    expect(await screen.findByText('Sistemas')).toBeInTheDocument()
    expect(screen.getByText('Finanzas')).toBeInTheDocument()
  })

  it('avisa cuando la empresa todavía no tiene departamentos', async () => {
    mockAccesos([])
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)

    expect(await screen.findByText(/todavía no hay departamentos/i)).toBeInTheDocument()
  })

  it('crea un departamento y lo agrega a la lista', async () => {
    const spy = mockAccesos([sistemas], (url, init) =>
      url === '/api/access/v1/departamentos' && init?.method === 'POST'
        ? json(finanzas, 201)
        : null,
    )
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)
    await screen.findByText('Sistemas')

    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/nombre del departamento/i), 'Finanzas')
    await user.click(screen.getByRole('button', { name: /agregar departamento/i }))

    expect(await screen.findByText('Finanzas')).toBeInTheDocument()
    const envio = spy.mock.calls.find(([, init]) => init?.method === 'POST')
    expect(JSON.parse(envio?.[1]?.body as string)).toEqual({ nombre: 'Finanzas' })
  })

  it('no deja repetir un departamento que ya existe', async () => {
    mockAccesos([sistemas])
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)
    await screen.findByText('Sistemas')

    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/nombre del departamento/i), 'sistemas')
    await user.click(screen.getByRole('button', { name: /agregar departamento/i }))

    expect(await screen.findByText(/ya existe/i)).toBeInTheDocument()
  })

  it('invita a un usuario con su rol en el segundo paso', async () => {
    const spy = mockAccesos([sistemas], (url, init) =>
      url === '/api/access/v1/usuarios' && init?.method === 'POST' ? json(invitado, 201) : null,
    )
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)
    await screen.findByText('Sistemas')

    const user = userEvent.setup()
    await continuar(user)

    await user.type(screen.getByLabelText(/^nombre$/i), 'Lucía Ponce')
    await user.type(screen.getByLabelText(/^correo$/i), 'lucia@acme.com')
    await user.click(screen.getByRole('button', { name: /enviar invitación/i }))

    expect(await screen.findByText('Lucía Ponce')).toBeInTheDocument()
    const envio = spy.mock.calls.find(
      ([url, init]) => url === '/api/access/v1/usuarios' && init?.method === 'POST',
    )
    expect(JSON.parse(envio?.[1]?.body as string)).toEqual({
      nombre: 'Lucía Ponce',
      correo: 'lucia@acme.com',
      rol: 'usuario_final',
    })
  })

  it('valida el correo antes de invitar', async () => {
    mockAccesos()
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)
    await screen.findByText('Sistemas')

    const user = userEvent.setup()
    await continuar(user)
    await user.type(screen.getByLabelText(/^nombre$/i), 'Lucía Ponce')
    await user.type(screen.getByLabelText(/^correo$/i), 'no-es-un-correo')
    await user.click(screen.getByRole('button', { name: /enviar invitación/i }))

    expect(await screen.findByText(/correo válido/i)).toBeInTheDocument()
  })

  it('resume lo configurado y marca el onboarding como terminado', async () => {
    const perfil: UsuarioActual = { ...admin, onboarding_completed: true }
    const spy = mockAccesos([sistemas, finanzas], (url, init) =>
      url === '/api/access/v1/me/onboarding' && init?.method === 'PATCH' ? json(perfil) : null,
    )
    const onCompletado = vi.fn()
    render(<OnboardingWizard usuario={admin} onCompletado={onCompletado} onOmitir={vi.fn()} />)
    await screen.findByText('Sistemas')

    const user = userEvent.setup()
    await continuar(user)
    await continuar(user)

    const resumen = screen.getByRole('region', { name: /esto es lo que quedó configurado/i })
    expect(within(resumen).getByText('2')).toBeInTheDocument()
    expect(within(resumen).getByText(/catálogo de servicios y la matriz de sla/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /terminar configuración/i }))

    const envio = spy.mock.calls.find(([, init]) => init?.method === 'PATCH')
    expect(JSON.parse(envio?.[1]?.body as string)).toEqual({ completed: true })
    expect(onCompletado).toHaveBeenCalledWith(perfil)
  })

  it('avisa si el servicio rechaza el cierre del onboarding', async () => {
    mockAccesos([sistemas], (url, init) =>
      url === '/api/access/v1/me/onboarding' && init?.method === 'PATCH'
        ? json({ codigo: 'permiso_denegado', detalle: 'Tu rol no puede configurar la empresa.' }, 403)
        : null,
    )
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={vi.fn()} />)
    await screen.findByText('Sistemas')

    const user = userEvent.setup()
    await continuar(user)
    await continuar(user)
    await user.click(screen.getByRole('button', { name: /terminar configuración/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/no puede configurar la empresa/i)
  })

  it('permite dejar la configuración para después', async () => {
    mockAccesos()
    const onOmitir = vi.fn()
    render(<OnboardingWizard usuario={admin} onCompletado={vi.fn()} onOmitir={onOmitir} />)
    await screen.findByText('Sistemas')

    await userEvent.click(screen.getByRole('button', { name: /configurar después/i }))
    expect(onOmitir).toHaveBeenCalled()
  })
})
