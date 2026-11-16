import { useEffect, useRef, useState } from 'react'
import { ApiError } from '@/api/client'
import { verifyCompany } from '@/api/public'
import { Link } from '@/components/Link'
import { queryParam } from '@/lib/routing'
import { getTrackingToken } from './tracking'

type State =
  | { kind: 'loading' }
  | { kind: 'ok'; id: string; tracked: boolean }
  | { kind: 'error'; text: string }

export default function VerifyPage() {
  const [state, setState] = useState<State>({ kind: 'loading' })
  const started = useRef(false)

  useEffect(() => {
    // El token es de un solo uso: evita la doble ejecución de StrictMode en desarrollo
    if (started.current) return
    started.current = true
    const token = queryParam('token')
    if (!token) {
      setState({ kind: 'error', text: 'El enlace de verificación está incompleto.' })
      return
    }
    verifyCompany(token)
      .then((r) => setState({ kind: 'ok', id: r.id, tracked: getTrackingToken(r.id) !== null }))
      .catch((e: unknown) =>
        setState({
          kind: 'error',
          text:
            e instanceof ApiError && e.status === 400
              ? 'El enlace no es válido, ya se usó o expiró. Vuelve a registrar tu empresa.'
              : 'No se pudo verificar el correo. Inténtalo más tarde.',
        }),
      )
  }, [])

  return (
    <div className="mx-auto max-w-xl space-y-4 text-center" role="status" aria-live="polite">
      <h1 className="text-xl font-bold">Verificación de correo</h1>
      {state.kind === 'loading' && <p className="text-sm text-slate-600">Verificando…</p>}
      {state.kind === 'error' && (
        <>
          <p role="alert" className="text-sm text-red-700">
            {state.text}
          </p>
          <Link to="/registro" className="text-sm underline">
            Volver al registro
          </Link>
        </>
      )}
      {state.kind === 'ok' && (
        <>
          <p className="text-sm text-slate-700">
            ¡Correo verificado! Estamos creando tu help desk. Te enviaremos otro correo con el
            enlace para activar tu cuenta.
          </p>
          {state.tracked && (
            <Link to={`/estado/${state.id}`} className="text-sm underline">
              Ver el progreso
            </Link>
          )}
        </>
      )}
    </div>
  )
}
