import { useCallback, useEffect, useId, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  ClipboardCheck,
  Loader2,
  MailPlus,
  Plus,
  Rocket,
  UserPlus,
} from 'lucide-react'
import {
  completeOnboarding,
  createDepartment,
  inviteUser,
  listDepartments,
  listRoles,
} from '@/api/access'
import { mensajeDeError } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader } from '@/components/ui/card'
import { Field, Input, Select } from '@/components/ui/form'
import { cn } from '@/lib/utils'
import { NOMBRE_ROL } from './roles'
import type { Departamento, Rol, RolId, Usuario, UsuarioActual } from './types'

interface OnboardingWizardProps {
  /** Administrador de la sesión; el asistente solo se muestra si su onboarding sigue pendiente. */
  usuario: UsuarioActual
  /** Se llama al terminar con el perfil ya actualizado por el servicio. */
  onCompletado: (usuario: UsuarioActual) => void
  /** Cierra el asistente sin marcarlo como terminado; volverá a aparecer al siguiente ingreso. */
  onOmitir: () => void
}

const PASOS = [
  { id: 1, titulo: 'Departamentos', icono: Building2 },
  { id: 2, titulo: 'Usuarios', icono: UserPlus },
  { id: 3, titulo: 'Confirmación', icono: ClipboardCheck },
] as const

/**
 * Asistente de configuración inicial de la empresa (Figma · Página 05, issue #151).
 *
 * Se muestra una sola vez, cuando `GET /me` responde `onboarding_completed: false` y el rol
 * puede configurar la empresa. Al terminar llama a `PATCH /me/onboarding`.
 *
 * El catálogo de servicios y la matriz de SLA **no** están aquí a propósito: según
 * `docs/ARCHITECTURE.md` los guarda Eventos, y su contrato v1 los deja fuera de alcance
 * de forma explícita. Cuando ese servicio los exponga se agregan como pasos 2 y 3.
 */
export function OnboardingWizard({ usuario, onCompletado, onOmitir }: OnboardingWizardProps) {
  const idBase = useId()
  const [paso, setPaso] = useState(1)

  const [departamentos, setDepartamentos] = useState<Departamento[]>([])
  const [cargandoDepartamentos, setCargandoDepartamentos] = useState(true)
  const [errorDepartamentos, setErrorDepartamentos] = useState<string | null>(null)
  const [nombreDepartamento, setNombreDepartamento] = useState('')
  const [guardandoDepartamento, setGuardandoDepartamento] = useState(false)

  const [roles, setRoles] = useState<Rol[]>([])
  const [errorRoles, setErrorRoles] = useState<string | null>(null)
  const [invitados, setInvitados] = useState<Usuario[]>([])
  const [invitacion, setInvitacion] = useState({
    nombre: '',
    correo: '',
    rol: 'usuario_final' as RolId,
  })
  const [errorInvitacion, setErrorInvitacion] = useState('')
  const [invitando, setInvitando] = useState(false)

  const [terminando, setTerminando] = useState(false)
  const [errorFinal, setErrorFinal] = useState<string | null>(null)

  const cargarDepartamentos = useCallback(async () => {
    setCargandoDepartamentos(true)
    setErrorDepartamentos(null)
    try {
      const { resultados } = await listDepartments()
      setDepartamentos(resultados)
    } catch (e) {
      setErrorDepartamentos(
        mensajeDeError(e, 'No se pudieron cargar los departamentos de la empresa.'),
      )
    } finally {
      setCargandoDepartamentos(false)
    }
  }, [])

  useEffect(() => {
    void cargarDepartamentos()
  }, [cargarDepartamentos])

  const cargarRoles = useCallback(async () => {
    setErrorRoles(null)
    try {
      const { resultados } = await listRoles()
      setRoles(resultados)
    } catch (e) {
      setErrorRoles(mensajeDeError(e, 'No se pudo cargar el catálogo de roles.'))
    }
  }, [])

  useEffect(() => {
    if (paso === 2 && roles.length === 0 && errorRoles === null) void cargarRoles()
  }, [paso, roles.length, errorRoles, cargarRoles])

  async function agregarDepartamento() {
    const nombre = nombreDepartamento.trim()
    if (!nombre) return
    if (departamentos.some((d) => d.nombre.toLowerCase() === nombre.toLowerCase())) {
      setErrorDepartamentos('Ese departamento ya existe.')
      return
    }
    setGuardandoDepartamento(true)
    setErrorDepartamentos(null)
    try {
      const creado = await createDepartment(nombre)
      setDepartamentos((actuales) => [...actuales, creado])
      setNombreDepartamento('')
    } catch (e) {
      setErrorDepartamentos(mensajeDeError(e, 'No se pudo crear el departamento.'))
    } finally {
      setGuardandoDepartamento(false)
    }
  }

  async function enviarInvitacion() {
    const correo = invitacion.correo.trim().toLowerCase()
    const nombre = invitacion.nombre.trim()
    if (!nombre) {
      setErrorInvitacion('Escribe el nombre de la persona.')
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
      setErrorInvitacion('Escribe un correo válido.')
      return
    }
    setInvitando(true)
    setErrorInvitacion('')
    try {
      const creado = await inviteUser({ nombre, correo, rol: invitacion.rol })
      setInvitados((actuales) => [...actuales, creado])
      setInvitacion({ nombre: '', correo: '', rol: 'usuario_final' })
    } catch (e) {
      setErrorInvitacion(mensajeDeError(e, 'No se pudo enviar la invitación.'))
    } finally {
      setInvitando(false)
    }
  }

  async function terminar() {
    setTerminando(true)
    setErrorFinal(null)
    try {
      const perfil = await completeOnboarding()
      onCompletado(perfil)
    } catch (e) {
      setErrorFinal(mensajeDeError(e, 'No se pudo guardar la configuración. Inténtalo de nuevo.'))
    } finally {
      setTerminando(false)
    }
  }

  function nombreRol(id: RolId): string {
    return roles.find((rol) => rol.id === id)?.nombre ?? NOMBRE_ROL[id]
  }

  return (
    <div className="min-h-screen bg-slate-100 p-4 sm:p-8">
      <div className="mx-auto w-full max-w-3xl space-y-6">
        <header className="space-y-1">
          <Badge variant="info" className="w-fit">
            Configuración inicial
          </Badge>
          <h1 className="text-xl font-bold text-slate-900">
            Deja lista tu empresa en el Service Desk
          </h1>
          <p className="text-sm text-slate-600">
            Hola {usuario.nombre.split(' ')[0]}. Son tres pasos y puedes cambiar todo después desde
            Gestión de Accesos.
          </p>
        </header>

        <Card>
          <CardHeader className="gap-4">
            <ol aria-label="Pasos de la configuración" className="flex flex-col gap-3 sm:flex-row">
              {PASOS.map((item) => {
                const estado = item.id < paso ? 'hecho' : item.id === paso ? 'actual' : 'pendiente'
                const Icono = item.icono
                return (
                  <li
                    key={item.id}
                    aria-current={estado === 'actual' ? 'step' : undefined}
                    className="flex flex-1 items-center gap-2"
                  >
                    <span
                      aria-hidden="true"
                      className={cn(
                        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold',
                        estado === 'hecho' && 'border-primary bg-primary text-white',
                        estado === 'actual' &&
                          'border-primary bg-white text-primary ring-4 ring-indigo-100',
                        estado === 'pendiente' && 'border-slate-200 bg-white text-slate-400',
                      )}
                    >
                      {estado === 'hecho' ? <Check size={16} /> : <Icono size={16} />}
                    </span>
                    <span
                      className={cn(
                        'text-sm font-medium',
                        estado === 'pendiente' ? 'text-slate-400' : 'text-slate-800',
                      )}
                    >
                      {item.titulo}
                      <span className="sr-only">
                        {estado === 'hecho'
                          ? ' (completado)'
                          : estado === 'actual'
                            ? ' (paso actual)'
                            : ' (pendiente)'}
                      </span>
                    </span>
                  </li>
                )
              })}
            </ol>
          </CardHeader>

          <CardContent className="space-y-5 pt-6">
            {/* Paso 1 · Departamentos */}
            {paso === 1 && (
              <section aria-labelledby={`${idBase}-departamentos`} className="space-y-4">
                <div>
                  <h2
                    id={`${idBase}-departamentos`}
                    className="text-base font-semibold text-slate-800"
                  >
                    Áreas de tu empresa
                  </h2>
                  <CardDescription>
                    Sirven para saber a qué área pertenece cada persona y a quién escalarle sus
                    tickets.
                  </CardDescription>
                </div>

                <div className="flex items-end gap-3">
                  <Field
                    label="Nombre del departamento"
                    htmlFor={`${idBase}-dep`}
                    className="flex-1"
                    error={errorDepartamentos ?? undefined}
                  >
                    <Input
                      id={`${idBase}-dep`}
                      value={nombreDepartamento}
                      placeholder="Sistemas"
                      disabled={guardandoDepartamento}
                      invalid={Boolean(errorDepartamentos)}
                      aria-describedby={errorDepartamentos ? `${idBase}-dep-description` : undefined}
                      onChange={(event) => {
                        setNombreDepartamento(event.target.value)
                        setErrorDepartamentos(null)
                      }}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault()
                          void agregarDepartamento()
                        }
                      }}
                    />
                  </Field>
                  <Button
                    type="button"
                    onClick={() => void agregarDepartamento()}
                    disabled={guardandoDepartamento || !nombreDepartamento.trim()}
                  >
                    {guardandoDepartamento ? (
                      <Loader2 size={16} aria-hidden="true" className="animate-spin" />
                    ) : (
                      <Plus size={16} aria-hidden="true" />
                    )}
                    Agregar departamento
                  </Button>
                </div>

                {cargandoDepartamentos ? (
                  <p className="py-6 text-center text-sm text-slate-500">
                    Cargando departamentos…
                  </p>
                ) : departamentos.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-slate-500">
                    Todavía no hay departamentos. Agrega al menos el área que atenderá el Service
                    Desk.
                  </p>
                ) : (
                  <ul className="flex flex-wrap gap-2">
                    {departamentos.map((departamento) => (
                      <li key={departamento.id}>
                        <Badge variant="default">{departamento.nombre}</Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {/* Paso 2 · Usuarios */}
            {paso === 2 && (
              <section aria-labelledby={`${idBase}-usuarios`} className="space-y-4">
                <div>
                  <h2 id={`${idBase}-usuarios`} className="text-base font-semibold text-slate-800">
                    Invita a tu equipo
                  </h2>
                  <CardDescription>
                    Cada persona recibe un correo con su enlace de activación para definir su
                    contraseña.
                  </CardDescription>
                </div>

                {errorRoles && (
                  <div
                    role="alert"
                    className="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
                  >
                    <span>{errorRoles}</span>
                    <Button type="button" variant="outline" size="sm" onClick={() => void cargarRoles()}>
                      Reintentar
                    </Button>
                  </div>
                )}

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end">
                  <Field label="Nombre" htmlFor={`${idBase}-nombre`}>
                    <Input
                      id={`${idBase}-nombre`}
                      value={invitacion.nombre}
                      placeholder="Lucía Ponce"
                      onChange={(event) =>
                        setInvitacion((actual) => ({ ...actual, nombre: event.target.value }))
                      }
                    />
                  </Field>
                  <Field
                    label="Correo"
                    htmlFor={`${idBase}-correo`}
                    error={errorInvitacion || undefined}
                  >
                    <Input
                      id={`${idBase}-correo`}
                      type="email"
                      value={invitacion.correo}
                      placeholder="persona@empresa.com"
                      invalid={Boolean(errorInvitacion)}
                      aria-describedby={
                        errorInvitacion ? `${idBase}-correo-description` : undefined
                      }
                      onChange={(event) => {
                        setInvitacion((actual) => ({ ...actual, correo: event.target.value }))
                        setErrorInvitacion('')
                      }}
                    />
                  </Field>
                  <Field label="Rol" htmlFor={`${idBase}-rol`}>
                    <Select
                      id={`${idBase}-rol`}
                      value={invitacion.rol}
                      onChange={(event) =>
                        setInvitacion((actual) => ({
                          ...actual,
                          rol: event.target.value as RolId,
                        }))
                      }
                    >
                      {(roles.length > 0
                        ? roles.map((rol) => ({ id: rol.id, nombre: rol.nombre }))
                        : (Object.keys(NOMBRE_ROL) as RolId[]).map((id) => ({
                            id,
                            nombre: NOMBRE_ROL[id],
                          }))
                      ).map((rol) => (
                        <option key={rol.id} value={rol.id}>
                          {rol.nombre}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Button type="button" onClick={() => void enviarInvitacion()} disabled={invitando}>
                    {invitando ? (
                      <Loader2 size={16} aria-hidden="true" className="animate-spin" />
                    ) : (
                      <MailPlus size={16} aria-hidden="true" />
                    )}
                    Enviar invitación
                  </Button>
                </div>

                {invitados.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-slate-500">
                    Aún no invitas a nadie. Puedes hacerlo después desde Gestión de Accesos.
                  </p>
                ) : (
                  <ul className="divide-y divide-slate-100 rounded-lg border border-border">
                    {invitados.map((invitado) => (
                      <li key={invitado.id} className="flex items-center justify-between px-4 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-slate-800">
                            {invitado.nombre}
                          </p>
                          <p className="text-xs text-slate-500">{invitado.correo}</p>
                        </div>
                        <Badge variant="info">{nombreRol(invitado.rol)}</Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {/* Paso 3 · Confirmación */}
            {paso === 3 && (
              <section aria-labelledby={`${idBase}-resumen`} className="space-y-4">
                <div>
                  <h2 id={`${idBase}-resumen`} className="text-base font-semibold text-slate-800">
                    Esto es lo que quedó configurado
                  </h2>
                  <CardDescription>
                    Al confirmar, el Service Desk deja de mostrarte este asistente.
                  </CardDescription>
                </div>

                <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-border bg-slate-50 p-4">
                    <dt className="text-xs font-medium uppercase text-slate-500">Departamentos</dt>
                    <dd className="mt-1 text-2xl font-bold text-slate-800">
                      {departamentos.length}
                    </dd>
                    <dd className="mt-1 text-xs text-slate-500">
                      {departamentos.map((d) => d.nombre).join(', ') || 'Ninguno'}
                    </dd>
                  </div>
                  <div className="rounded-lg border border-border bg-slate-50 p-4">
                    <dt className="text-xs font-medium uppercase text-slate-500">Invitaciones</dt>
                    <dd className="mt-1 text-2xl font-bold text-slate-800">{invitados.length}</dd>
                    <dd className="mt-1 text-xs text-slate-500">
                      {invitados.length > 0 ? 'Pendientes de activar' : 'Ninguna'}
                    </dd>
                  </div>
                </dl>

                <p className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-700">
                  El catálogo de servicios y la matriz de SLA se configuran aparte: los guarda el
                  servicio de Eventos y su contrato v1 todavía no los expone.
                </p>

                {errorFinal && (
                  <p
                    role="alert"
                    className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
                  >
                    {errorFinal}
                  </p>
                )}
              </section>
            )}
          </CardContent>

          <CardFooter className="flex-col-reverse gap-3 border-t border-border/50 pt-6 sm:flex-row sm:justify-between">
            <div className="flex w-full gap-3 sm:w-auto">
              <Button
                type="button"
                variant="outline"
                className="flex-1 sm:flex-none"
                disabled={paso === 1}
                onClick={() => setPaso((actual) => Math.max(1, actual - 1))}
              >
                <ArrowLeft size={16} aria-hidden="true" />
                Volver
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="flex-1 sm:flex-none"
                onClick={onOmitir}
              >
                Configurar después
              </Button>
            </div>

            {paso < PASOS.length ? (
              <Button
                type="button"
                className="w-full sm:w-auto"
                onClick={() => setPaso((actual) => actual + 1)}
              >
                Continuar
                <ArrowRight size={16} aria-hidden="true" />
              </Button>
            ) : (
              <Button
                type="button"
                className="w-full sm:w-auto"
                disabled={terminando}
                onClick={() => void terminar()}
              >
                {terminando ? (
                  <Loader2 size={16} aria-hidden="true" className="animate-spin" />
                ) : (
                  <Rocket size={16} aria-hidden="true" />
                )}
                Terminar configuración
              </Button>
            )}
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
