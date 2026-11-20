// Disponibilidad de subdominios, compartida por la landing y el registro.
import { useEffect, useState } from 'react'
import { SUBDOMINIO_REGEX, checkSubdomain } from '@/api/public'

export type Availability =
  'idle' | 'checking' | 'ok' | 'ocupado' | 'reservado' | 'invalido' | 'error'

export const AVAILABILITY_TEXT: Record<Availability, string> = {
  idle: '',
  checking: 'Comprobando disponibilidad…',
  ok: 'Disponible',
  ocupado: 'Ese subdominio ya está en uso.',
  reservado: 'Ese nombre está reservado.',
  invalido: 'Usa 3 a 30 caracteres: minúsculas, números y guiones.',
  error: 'No se pudo comprobar ahora; se validará al enviar.',
}

/** Estados que impiden registrar ese subdominio. */
export const BLOCKING: Availability[] = ['invalido', 'ocupado', 'reservado']

export function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9-]/g, '')
}

/** Consulta la disponibilidad en tiempo real, con espera para no llamar en cada tecla. */
export function useSubdomainAvailability(subdominio: string) {
  const [availability, setAvailability] = useState<Availability>('idle')

  useEffect(() => {
    if (!subdominio) {
      setAvailability('idle')
      return
    }
    if (!SUBDOMINIO_REGEX.test(subdominio)) {
      setAvailability('invalido')
      return
    }
    setAvailability('checking')
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      checkSubdomain(subdominio, controller.signal)
        .then((r) => setAvailability(r.disponible ? 'ok' : (r.motivo ?? 'ocupado')))
        .catch((e: unknown) => {
          if (!(e instanceof DOMException && e.name === 'AbortError')) setAvailability('error')
        })
    }, 400)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [subdominio])

  return [availability, setAvailability] as const
}
