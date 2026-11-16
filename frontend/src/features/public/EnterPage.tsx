import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '@/api/client'
import { lookupCompany } from '@/api/public'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getRuntimeConfig, tenantUrl } from '@/config/runtime'
import { inputClass } from './PublicLayout'

export default function EnterPage() {
  const [correo, setCorreo] = useState('')
  const [subdominio, setSubdominio] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function byEmail(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const r = await lookupCompany(correo.trim())
      window.location.assign(r.url)
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 404
          ? 'No encontramos una empresa para ese correo. Prueba con el subdominio de tu empresa.'
          : 'No se pudo buscar tu empresa. Inténtalo de nuevo.',
      )
      setBusy(false)
    }
  }

  function bySubdomain(event: FormEvent) {
    event.preventDefault()
    const sub = subdominio.trim().toLowerCase()
    if (sub) window.location.assign(tenantUrl(sub))
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-xl font-bold">Entrar a mi empresa</h1>
      <Card>
        <CardHeader>
          <CardTitle>Con tu correo</CardTitle>
          <CardDescription>Buscamos la empresa de tu correo corporativo.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={byEmail} className="space-y-3">
            <label className="block text-sm font-medium" htmlFor="correo">
              Correo
              <input
                id="correo"
                type="email"
                required
                className={inputClass}
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
              />
            </label>
            <Button type="submit" variant="primary" disabled={busy}>
              Buscar mi empresa
            </Button>
          </form>
          {error && (
            <p role="alert" className="mt-3 text-sm text-red-700">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Con el subdominio</CardTitle>
          <CardDescription>
            Si usas un correo personal (gmail, outlook…), escribe el subdominio de tu empresa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={bySubdomain} className="space-y-3">
            <label className="block text-sm font-medium" htmlFor="sub">
              Subdominio (…{`.${getRuntimeConfig().baseDomain}`})
              <input
                id="sub"
                required
                className={inputClass}
                value={subdominio}
                onChange={(e) => setSubdominio(e.target.value)}
              />
            </label>
            <Button type="submit" variant="secondary">
              Ir a mi empresa
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
