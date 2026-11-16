import { useEffect, useState } from 'react'
import { getCompanyStatus, type EstadoEmpresa } from '@/api/public'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getTrackingToken } from './tracking'

const FINAL = new Set(['activa', 'error', 'suspendida'])
const POLL_MS = 3000

const MESSAGES: Record<string, string> = {
  pendiente_verificacion:
    'Te enviamos un correo de verificación. Ábrelo para que empecemos a crear tu help desk.',
  aprovisionando:
    'Estamos creando tu help desk. Esto toma unos minutos; puedes dejar esta página abierta.',
  activa:
    'Tu help desk está listo. Revisa tu correo: te enviamos el enlace para activar tu cuenta.',
  suspendida: 'Esta empresa está suspendida. Contacta a soporte.',
  error:
    'Algo salió mal al crear tu help desk. Nuestro equipo lo revisará; puedes intentarlo de nuevo más tarde.',
}

export default function StatusPage({ id }: { id: string }) {
  const [status, setStatus] = useState<EstadoEmpresa | null>(null)
  const [failed, setFailed] = useState(false)
  const token = getTrackingToken(id)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    let timer: number | undefined
    const tick = async () => {
      try {
        const s = await getCompanyStatus(id, token)
        if (cancelled) return
        setStatus(s)
        setFailed(false)
        if (!FINAL.has(s.estado)) timer = window.setTimeout(tick, POLL_MS)
      } catch {
        if (cancelled) return
        setFailed(true)
        timer = window.setTimeout(tick, POLL_MS * 2)
      }
    }
    void tick()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [id, token])

  return (
    <div className="mx-auto max-w-xl">
      <Card>
        <CardHeader>
          <CardTitle>
            <h1 className="text-xl font-bold">Estado de tu registro</h1>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!token ? (
            <p role="alert" className="text-sm text-slate-700">
              Abre esta página desde el mismo navegador donde hiciste el registro. Si ya verificaste
              tu correo, espera el mensaje con el enlace de activación.
            </p>
          ) : (
            <div role="status" aria-live="polite" className="space-y-3">
              {!status && !failed && <p className="text-sm text-slate-600">Consultando…</p>}
              {failed && <p className="text-sm text-amber-700">Reintentando la conexión…</p>}
              {status && (
                <>
                  <p className="text-sm text-slate-700">
                    {status.mensaje ?? MESSAGES[status.estado]}
                  </p>
                  {status.estado === 'aprovisionando' && (
                    <progress className="h-2 w-full" aria-label="Creando tu help desk" />
                  )}
                  {status.estado === 'activa' && status.enlace_activacion && (
                    <a href={status.enlace_activacion} className="text-sm underline">
                      Activar mi cuenta ahora
                    </a>
                  )}
                  {status.estado === 'activa' && status.url && (
                    <p className="text-xs text-slate-500">Tu help desk: {status.url}</p>
                  )}
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
