import { ApiError } from '@/api/client'
import { NOMBRE_ROL } from './roles'
import type {
  InvitacionUsuario,
  Permiso,
  Rol,
  RolId,
  Sesion,
  Usuario,
  UsuarioActual,
} from './types'

/**
 * Datos simulados del módulo de Accesos, para trabajar mientras `services/access` no existe
 * (entregable de la fase 2: pantallas contra mocks, con estados de carga, vacío y error).
 *
 * La interfaz SIEMPRE llama primero a la API real; estos datos son el respaldo cuando el
 * microservicio no responde. Al levantarlo —o al correr `npm run mock:access`— desaparecen solos.
 * Para quitarlos de raíz en la fase 3, basta con borrar este archivo y las llamadas a `conRespaldo`.
 */

export const CLAVE_DEMO = 'helpchair-demo'

export const ROLES_SIMULADOS: Rol[] = [
  {
    id: 'administrador',
    nombre: NOMBRE_ROL.administrador,
    descripcion: 'Configura la empresa, el catálogo, los SLA y da de alta usuarios.',
    permisos: [
      'tickets:ver',
      'tickets:atender',
      'tickets:escalar',
      'empresa:configurar',
      'usuarios:administrar',
    ],
  },
  {
    id: 'agente_n2',
    nombre: NOMBRE_ROL.agente_n2,
    descripcion: 'Atiende incidencias escaladas y participa en la gestión de problemas.',
    permisos: ['tickets:ver', 'tickets:atender', 'tickets:escalar'],
  },
  {
    id: 'agente_n1',
    nombre: NOMBRE_ROL.agente_n1,
    descripcion: 'Primera línea del Service Desk: registra, clasifica y resuelve lo básico.',
    permisos: ['tickets:ver', 'tickets:atender'],
  },
  {
    id: 'usuario_final',
    nombre: NOMBRE_ROL.usuario_final,
    descripcion: 'Levanta peticiones del catálogo y consulta el avance de las suyas.',
    permisos: ['tickets:ver'],
  },
]

export const USUARIOS_SIMULADOS: Usuario[] = [
  {
    id: 'usr-001',
    nombre: 'Admin Help Desk',
    correo: 'admin@empresa15.com',
    rol: 'administrador',
    departamento: 'Sistemas',
    estado: 'activo',
    ultimo_acceso: '2026-11-16T15:12:00.000Z',
  },
  {
    id: 'usr-002',
    nombre: 'Daniela Ruiz',
    correo: 'daniela.ruiz@empresa15.com',
    rol: 'agente_n1',
    departamento: 'Sistemas',
    estado: 'activo',
    ultimo_acceso: '2026-11-16T14:40:00.000Z',
  },
  {
    id: 'usr-003',
    nombre: 'Marco Estrada',
    correo: 'marco.estrada@empresa15.com',
    rol: 'agente_n2',
    departamento: 'Operaciones',
    estado: 'activo',
    ultimo_acceso: '2026-11-15T17:05:00.000Z',
  },
  {
    id: 'usr-004',
    nombre: 'Lucía Ponce',
    correo: 'lucia.ponce@empresa15.com',
    rol: 'usuario_final',
    departamento: 'Finanzas',
    estado: 'activo',
    ultimo_acceso: '2026-11-16T09:30:00.000Z',
  },
  {
    id: 'usr-005',
    nombre: 'Hugo Navarro',
    correo: 'hugo.navarro@empresa15.com',
    rol: 'usuario_final',
    departamento: 'Ventas',
    estado: 'bloqueado',
    ultimo_acceso: '2026-11-10T11:22:00.000Z',
  },
  {
    id: 'usr-006',
    nombre: 'Sofía Marín',
    correo: 'sofia.marin@empresa15.com',
    rol: 'agente_n1',
    departamento: 'Sistemas',
    estado: 'invitado',
  },
]

function permisosDe(rol: RolId): Permiso[] {
  return ROLES_SIMULADOS.find((r) => r.id === rol)?.permisos ?? ['tickets:ver']
}

/**
 * Autenticación simulada. Cualquiera de los correos de arriba entra con `CLAVE_DEMO`;
 * reproduce los mismos errores del contrato para poder probar la pantalla completa.
 */
export function autenticarSimulado(correo: string, password: string): Sesion {
  const usuario = USUARIOS_SIMULADOS.find(
    (u) => u.correo.toLowerCase() === correo.trim().toLowerCase(),
  )
  if (!usuario || password !== CLAVE_DEMO) {
    throw new ApiError(401, 'Correo o contraseña incorrectos.', 'credenciales_invalidas')
  }
  if (usuario.estado === 'bloqueado') {
    throw new ApiError(423, 'Cuenta bloqueada por intentos fallidos.', 'cuenta_bloqueada')
  }
  if (usuario.estado === 'invitado') {
    throw new ApiError(403, 'La invitación sigue pendiente de activación.', 'cuenta_no_activada')
  }
  const actual: UsuarioActual = {
    ...usuario,
    permisos: permisosDe(usuario.rol),
    onboarding_completed: true,
  }
  return {
    acceso: `simulado.${usuario.id}`,
    refresco: `simulado.refresco.${usuario.id}`,
    token_tipo: 'Bearer',
    expira_en: 900,
    usuario: actual,
  }
}

export function filtrarSimulados(filtros: { buscar?: string; rol?: string }): Usuario[] {
  const texto = filtros.buscar?.trim().toLowerCase() ?? ''
  return USUARIOS_SIMULADOS.filter((usuario) => {
    const coincideTexto =
      !texto ||
      usuario.nombre.toLowerCase().includes(texto) ||
      usuario.correo.toLowerCase().includes(texto)
    return coincideTexto && (!filtros.rol || usuario.rol === filtros.rol)
  })
}

export function invitacionSimulada(invitacion: InvitacionUsuario): Usuario {
  return {
    id: `usr-${String(USUARIOS_SIMULADOS.length + 1).padStart(3, '0')}`,
    nombre: invitacion.nombre,
    correo: invitacion.correo,
    rol: invitacion.rol,
    departamento: invitacion.departamento ?? null,
    estado: 'invitado',
  }
}

/** Un `fetch` que no llega a ningún lado, o un servicio caído: ahí sí entra el respaldo. */
function servicioInalcanzable(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 404 || error.status >= 500
  return true
}

/**
 * Llama a la API real y, solo si el microservicio no responde, devuelve los datos simulados.
 * Un 401 o un 409 del servicio real se propagan: son respuestas legítimas, no una caída.
 */
export async function conRespaldo<T>(
  llamada: () => Promise<T>,
  respaldo: () => T,
): Promise<{ datos: T; simulado: boolean }> {
  try {
    return { datos: await llamada(), simulado: false }
  } catch (error) {
    if (!servicioInalcanzable(error)) throw error
    return { datos: respaldo(), simulado: true }
  }
}
