// Endpoints de Accesos usados por el sitio. Contrato: contracts/access/openapi.yaml.
import { apiPost } from './client'

/** Activa la cuenta del administrador inicial con el token del correo (un solo uso). */
export function activateAccount(token: string, password: string) {
  return apiPost<void>('/api/access/v1/activate', { token, password })
}
