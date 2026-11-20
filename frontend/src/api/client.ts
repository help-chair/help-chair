// Minimal HTTP client for the frontend. Types are generated from contracts/<servicio>/openapi.yaml.
// Paths are relative (/api/...), no hard‑coded base URL in the bundle and no CORS.
// In development the Vite proxy forwards requests; in production the gateway/ingress handles them.
// VITE_API_BASE_URL can be set to override the base URL (e.g., for testing).

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

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

interface ErrorBody {
  codigo?: string
  detalle?: string
  campos?: Record<string, string>
}

export interface ClientRequestInit extends RequestInit {
  _retry?: boolean
}

function shouldRefreshToken(path: string): boolean {
  return (
    !path.includes('/login') &&
    !path.includes('/refresh') &&
    !path.includes('/activate') &&
    !path.startsWith('/api/public')
  )
}

let refreshingPromise: Promise<boolean> | null = null

/** Refresh the JWT when a 401 is received on an authenticated endpoint.
 * Returns true if the token was refreshed, false otherwise.
 */
async function handleAuthError(): Promise<boolean> {
  if (refreshingPromise) {
    return refreshingPromise
  }

  refreshingPromise = (async () => {
    try {
      const { refreshSession, setAccessToken, setRefreshToken, getRefreshToken } =
        await import('./access')
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
      const { setAccessToken, setRefreshToken } = await import('./access')
      setAccessToken(null)
      setRefreshToken(null)
      return false
    } finally {
      refreshingPromise = null
    }
  })()

  return refreshingPromise
}

async function toApiError(method: string, path: string, response: Response): Promise<ApiError> {
  let body: ErrorBody = {}
  try {
    body = (await response.json()) as ErrorBody
  } catch {
    // response is not JSON
  }
  return new ApiError(
    response.status,
    body.detalle ?? `${method} ${path} → ${response.status}`,
    body.codigo,
    body.campos,
  )
}

export async function apiGet<T>(path: string, init?: ClientRequestInit): Promise<T> {
  const { _retry, ...fetchInit } = init ?? {}
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchInit,
    headers: { Accept: 'application/json', ...fetchInit?.headers },
  })
  if (!response.ok) {
    if (response.status === 401 && shouldRefreshToken(path) && !_retry) {
      const refreshed = await handleAuthError()
      if (refreshed) {
        // Retry once with new token
        return apiGet<T>(path, { ...init, _retry: true })
      }
    }
    throw await toApiError('GET', path, response)
  }
  return (await response.json()) as T
}

export async function apiPost<T>(path: string, body: unknown, init?: ClientRequestInit): Promise<T> {
  return send<T>('POST', path, body, init)
}

export async function apiPatch<T>(path: string, body: unknown, init?: ClientRequestInit): Promise<T> {
  return send<T>('PATCH', path, body, init)
}

async function send<T>(
  method: 'POST' | 'PATCH',
  path: string,
  body: unknown,
  init?: ClientRequestInit,
): Promise<T> {
  const { _retry, ...fetchInit } = init ?? {}
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchInit,
    method,
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...fetchInit?.headers },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    if (response.status === 401 && shouldRefreshToken(path) && !_retry) {
      const refreshed = await handleAuthError()
      if (refreshed) {
        return send<T>(method, path, body, { ...init, _retry: true })
      }
    }
    throw await toApiError(method, path, response)
  }
  if (response.status === 204) return undefined as unknown as T
  return (await response.json()) as T
}
