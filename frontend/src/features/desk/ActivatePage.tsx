import { useState } from 'react'
import type { FormEvent } from 'react'
import { activateAccount } from '@/api/access'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { queryParam } from '@/lib/routing'

const MIN_LENGTH = 12

/** /activar?token=… en el subdominio de la empresa: el administrador define su contraseña. */
export default function ActivatePage() {
  const token = queryParam('token')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (password.length < MIN_LENGTH) return setError(`Usa al menos ${MIN_LENGTH} caracteres.`)
    if (password !== confirm) return setError('Las contraseñas no coinciden.')
    setBusy(true)
    try {
      await activateAccount(token ?? '', password)
      setDone(true)
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 400
          ? e.message || 'El enlace no es válido, ya se usó o expiró.'
          : 'No se pudo activar la cuenta. Inténtalo de nuevo.',
      )
    } finally {
      setBusy(false)
    }
  }

  const field = 'mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'

  return (
    <main className="mx-auto max-w-md px-4 py-16">
      <Card>
        <CardHeader>
          <CardTitle>
            <h1 className="text-xl font-bold">Activa tu cuenta</h1>
          </CardTitle>
          <CardDescription>Define la contraseña del administrador de tu help desk.</CardDescription>
        </CardHeader>
        <CardContent>
          {!token ? (
            <p role="alert" className="text-sm text-red-700">
              El enlace de activación está incompleto.
            </p>
          ) : done ? (
            <div className="space-y-3" role="status">
              <p className="text-sm text-slate-700">¡Listo! Ya puedes iniciar sesión.</p>
              <a href="/" className="text-sm underline">
                Ir al inicio de sesión
              </a>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <label className="block text-sm font-medium" htmlFor="password">
                Contraseña
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={field}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              <label className="block text-sm font-medium" htmlFor="confirm">
                Repite la contraseña
                <input
                  id="confirm"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={field}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                />
              </label>
              {error && (
                <p role="alert" className="text-sm text-red-700">
                  {error}
                </p>
              )}
              <Button type="submit" variant="primary" disabled={busy}>
                Activar cuenta
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
