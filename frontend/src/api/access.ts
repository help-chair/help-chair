// Endpoints de Accesos usados por el sitio. Contrato: contracts/access/openapi.yaml.
import { apiGet, apiPatch, apiPost } from './client'
import type {
  ActualizacionUsuario,
  Credenciales,
  Departamento,
  InvitacionUsuario,
  Rol,
  Sesion,
  Usuario,
  UsuarioActual,
} from '@/features/access/types'

const BASE = '/api/access/v1'

/**
 * Token de acceso de la sesión. Vive SOLO en memoria: `AGENTS.md` prohíbe guardar credenciales en
 * localStorage/sessionStorage, así que al recargar la página hay que volver a iniciar sesión.
 * Cuando Accesos entregue el token de refresco en una cookie httpOnly, la sesión sobrevivirá
 * a la recarga sin exponer nada al JavaScript de la página.
 */
let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

function authHeader(): Record<string, string> {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
}

// --- Autenticación ---

export function login(credenciales: Credenciales) {
  return apiPost<Sesion>(`${BASE}/login`, credenciales)
}

export function refreshSession(refresco: string) {
  return apiPost<Sesion>(`${BASE}/refresh`, { refresco })
}

export function logout(refresco: string) {
  return apiPost<void>(`${BASE}/logout`, { refresco }, { headers: authHeader() })
}

// --- Cuenta ---

/** Activa la cuenta del administrador inicial con el token del correo (un solo uso). */
export function activateAccount(token: string, password: string) {
  return apiPost<void>(`${BASE}/activate`, { token, password })
}

export function getCurrentUser() {
  return apiGet<UsuarioActual>(`${BASE}/me`, { headers: authHeader() })
}

/** Marca el onboarding como terminado al guardar el último paso del asistente. */
export function completeOnboarding() {
  return apiPatch<UsuarioActual>(
    `${BASE}/me/onboarding`,
    { completed: true },
    { headers: authHeader() },
  )
}

// --- Usuarios, roles y departamentos ---

export function listUsers(filtros: { rol?: string; estado?: string; buscar?: string } = {}) {
  const query = new URLSearchParams()
  if (filtros.rol) query.set('rol', filtros.rol)
  if (filtros.estado) query.set('estado', filtros.estado)
  if (filtros.buscar) query.set('buscar', filtros.buscar)
  const sufijo = query.toString()
  return apiGet<{ resultados: Usuario[] }>(`${BASE}/usuarios${sufijo ? `?${sufijo}` : ''}`, {
    headers: authHeader(),
  })
}

export function inviteUser(invitacion: InvitacionUsuario) {
  return apiPost<Usuario>(`${BASE}/usuarios`, invitacion, { headers: authHeader() })
}

export function updateUser(id: string, cambios: ActualizacionUsuario) {
  return apiPatch<Usuario>(`${BASE}/usuarios/${encodeURIComponent(id)}`, cambios, {
    headers: authHeader(),
  })
}

/** Levanta el bloqueo por intentos fallidos y reinicia el contador. */
export function unlockUser(id: string) {
  return apiPost<Usuario>(
    `${BASE}/usuarios/${encodeURIComponent(id)}/desbloquear`,
    {},
    { headers: authHeader() },
  )
}

export function listRoles() {
  return apiGet<{ resultados: Rol[] }>(`${BASE}/roles`, { headers: authHeader() })
}

export function listDepartments() {
  return apiGet<{ resultados: Departamento[] }>(`${BASE}/departamentos`, { headers: authHeader() })
}
