import { seccionInicial, seccionesVisibles } from './navegacion'
import type { Permiso, RolId } from './types'

/** Permisos de cada rol tal como los devuelve GET /api/access/v1/roles. */
const PERMISOS: Record<RolId, Permiso[]> = {
  administrador: [
    'tickets:ver',
    'tickets:atender',
    'tickets:escalar',
    'empresa:configurar',
    'usuarios:administrar',
  ],
  agente_n2: ['tickets:ver', 'tickets:atender', 'tickets:escalar'],
  agente_n1: ['tickets:ver', 'tickets:atender'],
  usuario_final: ['tickets:ver'],
}

function permisosDe(rol: RolId) {
  return PERMISOS[rol]
}

describe('navegación según rol', () => {
  it('el administrador ve todas las secciones', () => {
    const secciones = seccionesVisibles(permisosDe('administrador'))
    expect(secciones).toEqual(
      expect.arrayContaining([
        'dashboard',
        'events',
        'requests',
        'incidents',
        'problems',
        'knowledge',
        'access',
      ]),
    )
  })

  it('el usuario final solo ve lo que puede usar', () => {
    const secciones = seccionesVisibles(permisosDe('usuario_final'))
    expect(secciones).toEqual(['dashboard', 'requests', 'knowledge'])
  })

  it('el agente N1 atiende tickets pero no administra accesos ni problemas', () => {
    const secciones = seccionesVisibles(permisosDe('agente_n1'))
    expect(secciones).toContain('incidents')
    expect(secciones).toContain('events')
    expect(secciones).not.toContain('problems')
    expect(secciones).not.toContain('access')
  })

  it('el agente N2 sí entra a problemas', () => {
    expect(seccionesVisibles(permisosDe('agente_n2'))).toContain('problems')
  })

  it('la sección inicial siempre es una que el rol puede ver', () => {
    for (const rol of ['administrador', 'agente_n2', 'agente_n1', 'usuario_final'] as RolId[]) {
      const permisos = permisosDe(rol)
      expect(seccionesVisibles(permisos)).toContain(seccionInicial(permisos))
    }
  })
})
