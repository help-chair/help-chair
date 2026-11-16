// Cliente HTTP mínimo. Los tipos se generarán a partir de contracts/<servicio>/openapi.yaml.
// Las rutas son RELATIVAS (/api/...): no hay URL de API incrustada en el bundle y no hay CORS.
// En desarrollo las reenvía el proxy de Vite; en producción, el gateway/ingress según el Host.
// VITE_API_BASE_URL solo existe como válvula de escape (p. ej. pruebas contra otra URL).
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

async function toApiError(method: string, path: string, response: Response): Promise<ApiError> {
  let body: ErrorBody = {}
  try {
    body = (await response.json()) as ErrorBody
  } catch {
    // la respuesta de error no es JSON
  }
  return new ApiError(
    response.status,
    body.detalle ?? `${method} ${path} → ${response.status}`,
    body.codigo,
    body.campos,
  )
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers },
  })
  if (!response.ok) throw await toApiError('GET', path, response)
  return (await response.json()) as T
}

export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...init?.headers },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw await toApiError('POST', path, response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
