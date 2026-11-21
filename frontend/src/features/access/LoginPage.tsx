import { useState } from 'react'
import type { FormEvent } from 'react'
import { Eye, EyeOff, LockKeyhole, LogIn, ShieldCheck } from 'lucide-react'
import { login, setAccessToken, setRefreshToken } from '@/api/access'
import { ApiError } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { Field, Input } from '@/components/ui/form'
import { CLAVE_DEMO, autenticarSimulado, conRespaldo } from './data'
import type { Sesion } from './types'

interface LoginPageProps {
  onAuthenticated: (sesion: Sesion) => void
}

type Errores = { correo?: string; password?: string }

/**
 * Inicio de sesión del Service Desk (Figma · Página 05, Gestión de Accesos).
 * Se muestra en el subdominio de la empresa cuando no hay sesión; la empresa la determina el stack,
 * no un campo del formulario.
 */
export default function LoginPage({ onAuthenticated }: LoginPageProps) {
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [verPassword, setVerPassword] = useState(false)
  const [errores, setErrores] = useState<Errores>({})
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null)
  const [bloqueada, setBloqueada] = useState(false)
  const [enviando, setEnviando] = useState(false)

  function validar(): Errores {
    const found: Errores = {}
    if (!correo.trim()) found.correo = 'Escribe tu correo de trabajo.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.trim()))
      found.correo = 'El correo no tiene un formato válido.'
    if (!password) found.password = 'Escribe tu contraseña.'
    return found
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const found = validar()
    setErrores(found)
    setErrorGeneral(null)
    if (Object.keys(found).length > 0) return

    setEnviando(true)
    try {
      // Si el microservicio de Accesos todavía no está arriba, se entra con los datos simulados.
      const { datos: sesion } = await conRespaldo(
        () => login({ correo: correo.trim(), password }),
        () => autenticarSimulado(correo, password),
      )
      setAccessToken(sesion.acceso)
      setRefreshToken(sesion.refresco)
      onAuthenticated(sesion)
    } catch (error) {
      setPassword('')
      if (error instanceof ApiError && error.status === 423) {
        setBloqueada(true)
        setErrorGeneral(
          error.message ||
            'Tu cuenta quedó bloqueada por varios intentos fallidos. Pide a un administrador que la reactive.',
        )
      } else if (error instanceof ApiError && error.status === 403) {
        setErrorGeneral(
          error.message || 'La cuenta aún no se activa. Revisa el correo de activación.',
        )
      } else if (error instanceof ApiError && error.status === 401) {
        setErrorGeneral('Correo o contraseña incorrectos. Revísalos e inténtalo de nuevo.')
      } else {
        setErrorGeneral('No se pudo iniciar sesión. Inténtalo de nuevo en un momento.')
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-100 lg:flex-row">
      {/* Panel de marca */}
      <section className="flex flex-col justify-between bg-slate-900 p-8 text-slate-200 lg:w-2/5 lg:p-12">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary font-bold text-white shadow-md">
            HC
          </span>
          <div>
            <h1 className="text-base font-bold tracking-wide text-white">Help Chair</h1>
            <p className="text-xs text-slate-400">ITIL v4 Service Desk</p>
          </div>
        </div>

        <div className="hidden space-y-4 py-10 lg:block">
          <h2 className="text-2xl font-bold text-white">Punto único de contacto</h2>
          <p className="max-w-sm text-sm text-slate-300">
            Entra con la cuenta de tu empresa para registrar incidencias, levantar peticiones del
            catálogo y dar seguimiento a tus tickets.
          </p>
          <ul className="space-y-2 text-sm text-slate-300">
            <li className="flex items-center gap-2">
              <ShieldCheck size={16} aria-hidden="true" className="text-emerald-400" />
              Acceso por roles (RBAC) dentro del stack de tu empresa
            </li>
            <li className="flex items-center gap-2">
              <LockKeyhole size={16} aria-hidden="true" className="text-emerald-400" />
              Bloqueo automático tras varios intentos fallidos
            </li>
          </ul>
        </div>

        <p className="text-xs text-slate-500">
          Centro de Enseñanza Técnica Industrial · Equipo 2 (Accesos)
        </p>
      </section>

      {/* Formulario */}
      <main className="flex flex-1 items-center justify-center p-6 sm:p-10">
        <Card className="w-full max-w-md">
          <CardHeader className="gap-2">
            <Badge variant="info" className="w-fit">
              {window.location.host}
            </Badge>
            <h2 className="text-xl font-bold text-slate-900">Inicia sesión</h2>
            <CardDescription>
              Si no reconoces esta dirección, verifica que sea el subdominio de tu empresa.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form noValidate onSubmit={onSubmit} className="space-y-5">
              {errorGeneral && (
                <p
                  role="alert"
                  className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
                >
                  {errorGeneral}
                </p>
              )}

              <Field label="Correo de trabajo" htmlFor="correo" required error={errores.correo}>
                <Input
                  id="correo"
                  type="email"
                  autoComplete="username"
                  placeholder="nombre@empresa.com"
                  value={correo}
                  disabled={bloqueada}
                  invalid={Boolean(errores.correo)}
                  aria-describedby={errores.correo ? 'correo-description' : undefined}
                  onChange={(event) => {
                    setCorreo(event.target.value)
                    setErrores((current) => ({ ...current, correo: undefined }))
                  }}
                />
              </Field>

              <Field label="Contraseña" htmlFor="password" required error={errores.password}>
                <div className="relative">
                  <Input
                    id="password"
                    type={verPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="pr-11"
                    value={password}
                    disabled={bloqueada}
                    invalid={Boolean(errores.password)}
                    aria-describedby={errores.password ? 'password-description' : undefined}
                    onChange={(event) => {
                      setPassword(event.target.value)
                      setErrores((current) => ({ ...current, password: undefined }))
                    }}
                  />
                  <button
                    type="button"
                    disabled={bloqueada}
                    aria-label={verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    onClick={() => setVerPassword((current) => !current)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-slate-400 transition-colors hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                  >
                    {verPassword ? (
                      <EyeOff size={16} aria-hidden="true" />
                    ) : (
                      <Eye size={16} aria-hidden="true" />
                    )}
                  </button>
                </div>
              </Field>

              <Button type="submit" size="lg" className="w-full" disabled={bloqueada || enviando}>
                <LogIn size={16} aria-hidden="true" />
                {enviando ? 'Entrando…' : 'Entrar'}
              </Button>

              {import.meta.env.DEV && (
                <details className="rounded-lg border border-border bg-surface-muted text-xs text-slate-600">
                  <summary className="cursor-pointer select-none p-3 font-medium text-slate-700">
                    Cuentas de prueba (solo desarrollo)
                  </summary>
                  <div className="border-t border-border px-3 py-3">
                    <p className="mb-2 text-slate-500">
                      Contraseña de todas: <code className="font-mono">{CLAVE_DEMO}</code>
                    </p>
                    <table className="w-full text-left text-xs">
                      <caption className="sr-only">Correos de prueba por rol y caso</caption>
                      <thead>
                        <tr className="text-slate-500">
                          <th className="py-1 pr-2 font-medium">Correo</th>
                          <th className="py-1 pr-2 font-medium">Rol</th>
                          <th className="py-1 font-medium">Para probar</th>
                        </tr>
                      </thead>
                      <tbody className="align-top text-slate-600">
                        <tr>
                          <td className="py-1 pr-2 font-mono">admin@empresa15.com</td>
                          <td>Administrador</td>
                          <td>Todo el menú y Gestión de Accesos</td>
                        </tr>
                        <tr>
                          <td className="py-1 pr-2 font-mono">daniela.ruiz@empresa15.com</td>
                          <td>Agente N1</td>
                          <td>Eventos e Incidencias, sin Problemas ni Accesos</td>
                        </tr>
                        <tr>
                          <td className="py-1 pr-2 font-mono">marco.estrada@empresa15.com</td>
                          <td>Agente N2</td>
                          <td>Panel de área, Incidencias escaladas y Problemas</td>
                        </tr>
                        <tr>
                          <td className="py-1 pr-2 font-mono">lucia.ponce@empresa15.com</td>
                          <td>Usuario final</td>
                          <td>Autoservicio, Peticiones y Base de Conocimiento</td>
                        </tr>
                        <tr>
                          <td className="py-1 pr-2 font-mono">hugo.navarro@empresa15.com</td>
                          <td>Usuario final</td>
                          <td>Cuenta bloqueada (error)</td>
                        </tr>
                        <tr>
                          <td className="py-1 pr-2 font-mono">sofia.marin@empresa15.com</td>
                          <td>Agente N1</td>
                          <td>Invitado sin activar (error)</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </details>
              )}
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
