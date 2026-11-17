// Configuración de tiempo de ejecución y detección del sitio según el dominio.
// Una sola imagen sirve a help-chair.com (sitio público) y a empresaN.help-chair.com (Service Desk).

export type SiteMode = 'public' | 'desk'

export interface HostInfo {
  mode: SiteMode
  tenant: string | null
}

export interface RuntimeConfig {
  baseDomain: string
}

// Subdominios que nunca son una empresa (coinciden con la lista reservada del registro).
const RESERVED = new Set(['www', 'api', 'admin', 'app', 'mail', 'status', 'help', 'support'])

let config: RuntimeConfig = { baseDomain: 'localhost' }

export async function loadRuntimeConfig(): Promise<RuntimeConfig> {
  try {
    const response = await fetch('/config.json', { cache: 'no-store' })
    if (response.ok) {
      const data = (await response.json()) as { BASE_DOMAIN?: unknown }
      if (typeof data.BASE_DOMAIN === 'string' && data.BASE_DOMAIN) {
        config = { baseDomain: data.BASE_DOMAIN.toLowerCase() }
      }
    }
  } catch {
    // sin config.json se usan los valores por defecto
  }
  return config
}

export function getRuntimeConfig(): RuntimeConfig {
  return config
}

export function resolveHost(hostname: string, baseDomain: string, fallback: SiteMode): HostInfo {
  const host = hostname.toLowerCase()
  const base = baseDomain.toLowerCase()
  if (host === base || host === `www.${base}`) return { mode: 'public', tenant: null }
  if (host.endsWith(`.${base}`)) {
    const sub = host.slice(0, -(base.length + 1))
    if (sub.includes('.') || RESERVED.has(sub)) return { mode: 'public', tenant: null }
    return { mode: 'desk', tenant: sub }
  }
  return { mode: fallback, tenant: null }
}

function devOverride(): SiteMode | null {
  // Solo en desarrollo: http://localhost:5173/?site=public (o desk) cambia de sitio sin tocar DNS.
  if (!import.meta.env.DEV) return null
  try {
    const fromQuery = new URLSearchParams(window.location.search).get('site')
    if (fromQuery === 'public' || fromQuery === 'desk') {
      window.sessionStorage.setItem('hc-site', fromQuery)
      return fromQuery
    }
    const saved = window.sessionStorage.getItem('hc-site')
    return saved === 'public' || saved === 'desk' ? saved : null
  } catch {
    return null
  }
}

export function currentSite(): HostInfo {
  const override = devOverride()
  if (override) return { mode: override, tenant: null }
  // Host desconocido: en desarrollo se conserva el comportamiento actual (Service Desk);
  // en producción lo seguro es mostrar el sitio público.
  const fallback: SiteMode = import.meta.env.DEV ? 'desk' : 'public'
  return resolveHost(window.location.hostname, config.baseDomain, fallback)
}

/** URL del Service Desk de una empresa (mismo protocolo y puerto que la página actual). */
export function tenantUrl(subdomain: string): string {
  const { protocol, port } = window.location
  return `${protocol}//${subdomain}.${config.baseDomain}${port ? `:${port}` : ''}`
}
