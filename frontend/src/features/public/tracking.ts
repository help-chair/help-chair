// El token de seguimiento solo vive en la pestaña que hizo el registro (sessionStorage).
const key = (id: string) => `hc-track:${id}`

export function saveTrackingToken(id: string, token: string): void {
  try {
    window.sessionStorage.setItem(key(id), token)
  } catch {
    // sin sessionStorage el progreso no se puede consultar; el correo sigue funcionando
  }
}

export function getTrackingToken(id: string): string | null {
  try {
    return window.sessionStorage.getItem(key(id))
  } catch {
    return null
  }
}
