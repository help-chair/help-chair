// Tipos del módulo de Accesos, escritos a partir de contracts/access/openapi.yaml (v0.1.0).
// Si cambia el contrato, cambia primero este archivo.

/** Roles RBAC del stack. Catálogo en GET /api/access/v1/roles. */
export type RolId = 'administrador' | 'agente_n2' | 'agente_n1' | 'usuario_final'

export type Permiso =
  | 'tickets:ver'
  | 'tickets:atender'
  | 'tickets:escalar'
  | 'empresa:configurar'
  | 'usuarios:administrar'

export interface Rol {
  id: RolId
  nombre: string
  descripcion?: string
  permisos: Permiso[]
}

/**
 * `invitado`: creado sin contraseña, con activación pendiente.
 * `bloqueado`: por intentos fallidos. `suspendido`: dado de baja por un administrador.
 */
export type EstadoUsuario = 'activo' | 'invitado' | 'bloqueado' | 'suspendido'

export interface Usuario {
  id: string
  nombre: string
  correo: string
  rol: RolId
  departamento?: string | null
  estado: EstadoUsuario
  ultimo_acceso?: string | null
  creado_en?: string
}

/** GET /api/access/v1/me: el usuario de la sesión, con sus permisos efectivos. */
export interface UsuarioActual extends Usuario {
  permisos: Permiso[]
  onboarding_completed: boolean
}

/** Respuesta de POST /api/access/v1/login y /refresh. */
export interface Sesion {
  acceso: string
  refresco: string
  token_tipo: 'Bearer'
  expira_en: number
  usuario: UsuarioActual
}

export interface Credenciales {
  correo: string
  password: string
}

export interface InvitacionUsuario {
  nombre: string
  correo: string
  rol: RolId
  departamento?: string
}

export interface ActualizacionUsuario {
  rol?: RolId
  departamento?: string | null
  estado?: 'activo' | 'suspendido'
}

export interface Departamento {
  id: string
  nombre: string
  usuarios?: number
}

/** Códigos de error previstos en el contrato (campo `codigo` de la respuesta). */
export type CodigoError =
  | 'credenciales_invalidas'
  | 'cuenta_bloqueada'
  | 'cuenta_no_activada'
  | 'token_invalido'
  | 'no_autenticado'
  | 'permiso_denegado'
  | 'correo_duplicado'
  | 'administrador_existente'
  | 'ultimo_administrador'
  | 'departamento_duplicado'
