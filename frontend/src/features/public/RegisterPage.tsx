import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError } from '@/api/client'
import { registerCompany, type Tamano } from '@/api/public'
import { getRuntimeConfig } from '@/config/runtime'
import { navigate, queryParam } from '@/lib/routing'
import { inputClass } from './PublicLayout'
import { AVAILABILITY_TEXT, slugify, useSubdomainAvailability } from './subdomain'
import { saveTrackingToken } from './tracking'

const TAMANOS: Tamano[] = ['1-10', '11-50', '51-200', '201-1000', '1000+']

export default function RegisterPage() {
  const [nombre, setNombre] = useState('')
  // La landing puede enviar el subdominio elegido: /registro?subdominio=acme
  const [subdominio, setSubdominio] = useState(() => slugify(queryParam('subdominio') ?? ''))
  const [sector, setSector] = useState('')
  const [tamano, setTamano] = useState<Tamano | ''>('')
  const [pais, setPais] = useState('')
  const [adminNombre, setAdminNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [acepta, setAcepta] = useState(false)
  const [availability, setAvailability] = useSubdomainAvailability(subdominio)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const baseDomain = getRuntimeConfig().baseDomain

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!acepta) return
    setSubmitting(true)
    try {
      const created = await registerCompany({
        empresa: {
          nombre: nombre.trim(),
          subdominio,
          ...(sector.trim() && { sector: sector.trim() }),
          ...(tamano && { tamano }),
          ...(pais.trim() && { pais: pais.trim().toUpperCase() }),
        },
        administrador: { nombre: adminNombre.trim(), correo: correo.trim() },
        acepta_terminos: true,
      })
      saveTrackingToken(created.id, created.token_seguimiento)
      navigate(`/estado/${created.id}`)
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) setAvailability('ocupado')
      setError(
        e instanceof ApiError
          ? e.status === 429
            ? 'Demasiados intentos. Espera unos minutos e inténtalo de nuevo.'
            : e.message
          : 'No se pudo enviar el registro. Inténtalo de nuevo.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  const availabilityClass =
    availability === 'ok'
      ? 'text-emerald-700'
      : availability === 'checking'
        ? 'text-slate-500'
        : 'text-red-700'
  const canSubmit =
    acepta && availability !== 'invalido' && availability !== 'ocupado' && !submitting

  return (
    <div className="mx-auto max-w-xl">
      <Card>
        <CardHeader>
          <CardTitle>
            <h1 className="text-xl font-bold">Registrar mi empresa</h1>
          </CardTitle>
          <CardDescription>
            Solo pedimos lo mínimo. Servicios, SLA y usuarios los configurarás después, dentro de tu
            help desk.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4" noValidate={false}>
            <label className="block text-sm font-medium" htmlFor="nombre">
              Nombre de la empresa
              <input
                id="nombre"
                required
                maxLength={120}
                className={inputClass}
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </label>

            <div>
              <label className="block text-sm font-medium" htmlFor="subdominio">
                Subdominio
              </label>
              <div className="flex items-center gap-2">
                <input
                  id="subdominio"
                  required
                  minLength={3}
                  maxLength={30}
                  className={inputClass}
                  value={subdominio}
                  aria-describedby="subdominio-estado"
                  onChange={(e) => setSubdominio(slugify(e.target.value))}
                />
                <span className="mt-1 whitespace-nowrap text-sm text-slate-500">.{baseDomain}</span>
              </div>
              <p
                id="subdominio-estado"
                role="status"
                aria-live="polite"
                className={`mt-1 text-xs ${availabilityClass}`}
              >
                {AVAILABILITY_TEXT[availability]}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <label className="block text-sm font-medium" htmlFor="sector">
                Sector (opcional)
                <input
                  id="sector"
                  maxLength={60}
                  className={inputClass}
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                />
              </label>
              <label className="block text-sm font-medium" htmlFor="tamano">
                Empleados (opcional)
                <select
                  id="tamano"
                  className={inputClass}
                  value={tamano}
                  onChange={(e) => setTamano(e.target.value as Tamano | '')}
                >
                  <option value="">—</option>
                  {TAMANOS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm font-medium" htmlFor="pais">
                País (opcional)
                <input
                  id="pais"
                  maxLength={2}
                  placeholder="MX"
                  className={inputClass}
                  value={pais}
                  onChange={(e) => setPais(e.target.value)}
                />
              </label>
            </div>

            <label className="block text-sm font-medium" htmlFor="admin-nombre">
              Tu nombre (administrador)
              <input
                id="admin-nombre"
                required
                maxLength={120}
                className={inputClass}
                value={adminNombre}
                onChange={(e) => setAdminNombre(e.target.value)}
              />
            </label>
            <label className="block text-sm font-medium" htmlFor="correo">
              Tu correo
              <input
                id="correo"
                type="email"
                required
                className={inputClass}
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
              />
            </label>

            <label className="flex items-start gap-2 text-sm" htmlFor="terminos">
              <input
                id="terminos"
                type="checkbox"
                className="mt-1"
                checked={acepta}
                onChange={(e) => setAcepta(e.target.checked)}
              />
              Acepto los términos de uso.
            </label>

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
              >
                {error}
              </p>
            )}

            <Button type="submit" variant="primary" disabled={!canSubmit}>
              {submitting ? 'Enviando…' : 'Crear mi help desk'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
