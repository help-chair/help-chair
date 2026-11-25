// Cliente HTTP mínimo del frontend. Los tipos salen de contracts/<servicio>/openapi.yaml.
// Las rutas son relativas (/api/...): sin URL base fija en el bundle y sin CORS.
// En desarrollo las reenvía el proxy de Vite; en testing y producción, el ingress según el Host.
// VITE_API_BASE_URL permite cambiar la base (p. ej. en pruebas).
import {
  getAccessToken,
  getRefreshToken,
  refreshSession,
  setAccessToken,
  setRefreshToken,
} from './access'

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

/** Tiempo máximo de espera de una respuesta antes de darla por perdida. */
export const TIEMPO_LIMITE_MS = 15_000

/**
 * Error de la API. `status` es el código HTTP; vale `0` cuando no hubo respuesta
 * (sin red, servicio caído o tiempo de espera agotado).
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public fields?: Record<string, string>,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** true cuando la petición no obtuvo respuesta del servicio (red, caída o tiempo agotado). */
export function esErrorDeConexion(error: unknown): boolean {
  return error instanceof ApiError && error.status === 0
}

/** Mensaje claro para la interfaz: el de la `ApiError` o, si es otro error, el respaldo dado. */
export function mensajeDeError(error: unknown, respaldo: string): string {
  return error instanceof ApiError && error.message ? error.message : respaldo
}

/** Mensaje cuando el servicio responde con error pero sin `detalle`. */
function mensajePorEstado(status: number): string {
  if (status === 401) return 'Tu sesión expiró. Vuelve a iniciar sesión.'
  if (status === 403) return 'Tu rol no tiene permiso para esta acción.'
  if (status === 404) return 'No se encontró el recurso o el servicio no está publicado.'
  if (status === 408 || status === 504) {
    return 'El servicio tardó demasiado en responder. Inténtalo de nuevo en un momento.'
  }
  if (status >= 500) return 'El servicio tuvo un error interno. Inténtalo de nuevo en un momento.'
  return `La solicitud no se pudo completar (código ${status}).`
}

export interface ClientRequestInit extends RequestInit {
  _retry?: boolean
}

type Metodo = 'GET' | 'POST' | 'PATCH' | 'DELETE'

function shouldRefreshToken(path: string): boolean {
  return (
    !path.includes('/login') &&
    !path.includes('/refresh') &&
    !path.includes('/activate') &&
    !path.startsWith('/api/public')
  )
}

/** El JWT de Accesos viaja en todas las llamadas del Service Desk, nunca en la API pública. */
function cabeceraDeSesion(path: string): Record<string, string> {
  if (path.startsWith('/api/public')) return {}
  const token = getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

let refreshingPromise: Promise<boolean> | null = null

/** Refresca el JWT tras un 401 en un endpoint autenticado. Devuelve true si se renovó. */
async function handleAuthError(): Promise<boolean> {
  if (refreshingPromise) {
    return refreshingPromise
  }

  refreshingPromise = (async () => {
    try {
      const refresco = getRefreshToken()
      if (!refresco) {
        setAccessToken(null)
        setRefreshToken(null)
        return false
      }
      const refreshed = await refreshSession(refresco)
      setAccessToken(refreshed.acceso)
      setRefreshToken(refreshed.refresco)
      return true
    } catch {
      // Si el refresco falla, limpia ambos tokens para que la UI fuerce el login.
      setAccessToken(null)
      setRefreshToken(null)
      return false
    } finally {
      refreshingPromise = null
    }
  })()

  return refreshingPromise
}

interface ErrorBody {
  codigo?: unknown
  detalle?: unknown
  campos?: unknown
  detail?: unknown
  [campo: string]: unknown
}

/**
 * Lee el cuerpo de error. Acepta el formato de los contratos (`{codigo, detalle, campos}`)
 * y el de Django REST Framework (`{detail}` o `{campo: ["mensaje"]}`).
 */
function leerError(body: ErrorBody): {
  detalle?: string
  codigo?: string
  campos?: Record<string, string>
} {
  const codigo = typeof body.codigo === 'string' ? body.codigo : undefined
  if (typeof body.detalle === 'string') {
    const campos =
      body.campos && typeof body.campos === 'object'
        ? (body.campos as Record<string, string>)
        : undefined
    return { detalle: body.detalle, codigo, campos }
  }
  if (typeof body.detail === 'string') return { detalle: body.detail, codigo }

  const campos: Record<string, string> = {}
  for (const [campo, valor] of Object.entries(body)) {
    const mensaje = Array.isArray(valor) ? valor.find((v) => typeof v === 'string') : valor
    if (typeof mensaje === 'string') campos[campo] = mensaje
  }
  const primero = Object.values(campos)[0]
  return primero ? { detalle: primero, codigo, campos } : { codigo }
}

async function toApiError(response: Response): Promise<ApiError> {
  let body: ErrorBody = {}
  try {
    const leido: unknown = await response.json()
    if (leido && typeof leido === 'object') body = leido as ErrorBody
  } catch {
    // la respuesta no es JSON
  }
  const { detalle, codigo, campos } = leerError(body)
  return new ApiError(response.status, detalle ?? mensajePorEstado(response.status), codigo, campos)
}

/** Lee el JSON de una respuesta correcta; si llega otra cosa (p. ej. HTML), lo reporta claro. */
async function leerJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(
      response.status,
      'El servicio respondió en un formato inesperado. Verifica que esté publicado en el ingress.',
      'respuesta_invalida',
    )
  }
}

/** `fetch` con tiempo límite. Convierte los fallos de red en `ApiError` con `status` 0. */
async function ejecutar(path: string, init: RequestInit): Promise<Response> {
  const controlador = new AbortController()
  let agotado = false
  const temporizador = setTimeout(() => {
    agotado = true
    controlador.abort()
  }, TIEMPO_LIMITE_MS)
  const externa = init.signal
  const alAbortar = () => controlador.abort()
  if (externa) {
    if (externa.aborted) controlador.abort()
    else externa.addEventListener('abort', alAbortar, { once: true })
  }

  try {
    return await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controlador.signal })
  } catch (error) {
    // Si quien llamó canceló la petición, se respeta su AbortError tal cual.
    if (externa?.aborted) throw error
    if (agotado) {
      throw new ApiError(
        0,
        'El servicio tardó demasiado en responder. Inténtalo de nuevo en un momento.',
        'tiempo_agotado',
      )
    }
    throw new ApiError(
      0,
      'No hay conexión con el servicio. Revisa tu red o que el servicio esté disponible.',
      'sin_conexion',
    )
  } finally {
    clearTimeout(temporizador)
    externa?.removeEventListener('abort', alAbortar)
  }
}

async function request<T>(
  method: Metodo,
  path: string,
  body: unknown,
  init?: ClientRequestInit,
): Promise<T> {
  const { _retry, ...fetchInit } = init ?? {}
  const conCuerpo = body !== undefined
  const response = await ejecutar(path, {
    ...fetchInit,
    method,
    headers: {
      Accept: 'application/json',
      ...(conCuerpo ? { 'Content-Type': 'application/json' } : {}),
      ...cabeceraDeSesion(path),
      ...fetchInit.headers,
    },
    ...(conCuerpo ? { body: JSON.stringify(body) } : {}),
  })

  if (!response.ok) {
    if (response.status === 401 && shouldRefreshToken(path) && !_retry) {
      const refreshed = await handleAuthError()
      if (refreshed) {
        // Reintenta una sola vez; la cabecera se arma de nuevo con el token renovado.
        return request<T>(method, path, body, { ...init, _retry: true })
      }
    }
    throw await toApiError(response)
  }
  if (response.status === 204) return undefined as unknown as T
  return leerJson<T>(response)
}

export function apiGet<T>(path: string, init?: ClientRequestInit): Promise<T> {
  return request<T>('GET', path, undefined, init)
}

export function apiPost<T>(path: string, body: unknown, init?: ClientRequestInit): Promise<T> {
  return request<T>('POST', path, body, init)
}

export function apiPatch<T>(path: string, body: unknown, init?: ClientRequestInit): Promise<T> {
  return request<T>('PATCH', path, body, init)
}

export function apiDelete<T = void>(path: string, init?: ClientRequestInit): Promise<T> {
  return request<T>('DELETE', path, undefined, init)
}
