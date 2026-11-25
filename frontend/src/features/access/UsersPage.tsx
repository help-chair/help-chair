import { useCallback, useEffect, useState } from 'react'
import {
  KeyRound,
  Lock,
  MailPlus,
  Search,
  ShieldCheck,
  Unlock,
  UserCheck,
  UserX,
} from 'lucide-react'
import { inviteUser, listRoles, listUsers, unlockUser, updateUser } from '@/api/access'
import { ApiError, mensajeDeError } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, Input, Select } from '@/components/ui/form'
import { NOMBRE_ROL } from './roles'
import type { EstadoUsuario, Rol, RolId, Usuario, UsuarioActual } from './types'

interface UsersPageProps {
  /** Usuario de la sesión; sus permisos deciden qué acciones se muestran. */
  usuario: UsuarioActual
}

interface EstadoBadge {
  variant: 'success' | 'info' | 'exception' | 'default'
  label: string
}

const ESTADO_BADGE: Record<EstadoUsuario, EstadoBadge> = {
  activo: { variant: 'success', label: 'Activa' },
  invitado: { variant: 'info', label: 'Invitación pendiente' },
  bloqueado: { variant: 'exception', label: 'Bloqueada' },
  suspendido: { variant: 'default', label: 'Suspendida' },
}

function fechaCorta(valor?: string | null): string {
  if (!valor) return 'Nunca'
  return new Date(valor).toLocaleString('es-MX', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Vista de Gestión de Accesos dentro del Service Desk: usuarios, roles RBAC y bloqueos. */
export function UsersPage({ usuario }: UsersPageProps) {
  const puedeAdministrar = usuario.permisos.includes('usuarios:administrar')

  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  const [buscar, setBuscar] = useState('')
  const [filtroRol, setFiltroRol] = useState<RolId | ''>('')

  const [invitacion, setInvitacion] = useState({
    nombre: '',
    correo: '',
    rol: 'usuario_final' as RolId,
  })
  const [errorInvitacion, setErrorInvitacion] = useState('')

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    const filtros = { buscar: buscar.trim() || undefined, rol: filtroRol || undefined }
    try {
      const [respuestaUsuarios, respuestaRoles] = await Promise.all([
        listUsers(filtros),
        listRoles(),
      ])
      setUsuarios(respuestaUsuarios.resultados)
      setRoles(respuestaRoles.resultados)
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 403
          ? 'Tu rol no puede consultar el directorio de usuarios.'
          : `No se pudo cargar el directorio. ${mensajeDeError(e, 'Inténtalo de nuevo en un momento.')}`,
      )
    } finally {
      setCargando(false)
    }
  }, [buscar, filtroRol])

  useEffect(() => {
    const id = window.setTimeout(() => void cargar(), 250)
    return () => window.clearTimeout(id)
  }, [cargar])

  function nombreRol(id: RolId): string {
    return roles.find((rol) => rol.id === id)?.nombre ?? NOMBRE_ROL[id]
  }

  async function accion(trabajo: () => Promise<Usuario>, mensaje: (u: Usuario) => string) {
    setAviso(null)
    try {
      const actualizado = await trabajo()
      setUsuarios((actuales) =>
        actuales.map((u) => (u.id === actualizado.id ? actualizado : u)),
      )
      setAviso(mensaje(actualizado))
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : 'No se pudo completar la acción. Inténtalo de nuevo.',
      )
    }
  }

  async function enviarInvitacion() {
    const correo = invitacion.correo.trim().toLowerCase()
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
      setErrorInvitacion('Escribe un correo válido.')
      return
    }
    if (!invitacion.nombre.trim()) {
      setErrorInvitacion('Escribe el nombre de la persona.')
      return
    }
    setErrorInvitacion('')
    const datosInvitacion = { ...invitacion, correo, nombre: invitacion.nombre.trim() }
    try {
      const nuevo = await inviteUser(datosInvitacion)
      setUsuarios((actuales) => [...actuales, nuevo])
      setInvitacion({ nombre: '', correo: '', rol: 'usuario_final' })
      setAviso(`Invitación enviada a ${correo}.`)
    } catch (e) {
      setErrorInvitacion(
        e instanceof ApiError && e.status === 409
          ? 'Ese correo ya tiene cuenta en la empresa.'
          : mensajeDeError(e, 'No se pudo enviar la invitación.'),
      )
    }
  }

  return (
    <div className="space-y-6">
      {/* Banner de la práctica */}
      <div className="flex flex-col justify-between gap-4 rounded-xl border border-border bg-white p-6 shadow-sm md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-lg bg-indigo-50 p-2 text-primary">
              <ShieldCheck size={20} />
            </span>
            <h3 className="text-xl font-bold text-slate-900">
              Gestión de Accesos (Access Management)
            </h3>
          </div>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            Práctica ITIL v4 de Seguridad de la Información: quién entra al Service Desk, con
            qué rol y con qué permisos. Cada cambio publica un evento de seguridad hacia Eventos.
          </p>
        </div>
        <Badge variant="info">Equipo 2</Badge>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </p>
      )}
      {aviso && (
        <p
          role="status"
          className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700"
        >
          {aviso}
        </p>
      )}

      {/* Resumen de roles */}
      {roles.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          {roles.map((rol) => (
            <Card key={rol.id} className="p-5">
              <p className="text-xs font-semibold uppercase text-slate-500">{rol.nombre}</p>
              <p className="mt-1 text-2xl font-bold text-slate-800">
                {usuarios.filter((u) => u.rol === rol.id).length}
              </p>
              {rol.descripcion && <p className="mt-2 text-xs text-slate-500">{rol.descripcion}</p>}
            </Card>
          ))}
        </div>
      )}

      {/* Invitación */}
      {puedeAdministrar && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Invitar a un usuario</CardTitle>
            <CardDescription>
              Se crea la cuenta sin contraseña y se envía el enlace de activación por correo.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end">
            <Field label="Nombre" htmlFor="invitar-nombre">
              <Input
                id="invitar-nombre"
                value={invitacion.nombre}
                placeholder="Lucía Ponce"
                onChange={(event) =>
                  setInvitacion((actual) => ({ ...actual, nombre: event.target.value }))
                }
              />
            </Field>
            <Field label="Correo" htmlFor="invitar-correo" error={errorInvitacion}>
              <Input
                id="invitar-correo"
                type="email"
                value={invitacion.correo}
                placeholder="persona@empresa.com"
                invalid={Boolean(errorInvitacion)}
                onChange={(event) => {
                  setInvitacion((actual) => ({ ...actual, correo: event.target.value }))
                  setErrorInvitacion('')
                }}
              />
            </Field>
            <Field label="Rol" htmlFor="invitar-rol">
              <Select
                id="invitar-rol"
                value={invitacion.rol}
                onChange={(event) =>
                  setInvitacion((actual) => ({ ...actual, rol: event.target.value as RolId }))
                }
              >
                {roles.map((rol) => (
                  <option key={rol.id} value={rol.id}>
                    {rol.nombre}
                  </option>
                ))}
              </Select>
            </Field>
            <Button type="button" onClick={() => void enviarInvitacion()}>
              <MailPlus size={16} aria-hidden="true" />
              Invitar
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Directorio */}
      <Card className="overflow-hidden">
        <CardHeader className="gap-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <CardTitle className="text-base">Usuarios de la empresa</CardTitle>
              <CardDescription>{usuarios.length} cuentas</CardDescription>
            </div>
            <div className="flex flex-wrap items-end gap-3">
              <Field label="Buscar" htmlFor="buscar-usuario" className="w-56">
                <div className="relative">
                  <Search
                    size={16}
                    aria-hidden="true"
                    className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                  <Input
                    id="buscar-usuario"
                    type="search"
                    className="pl-9"
                    placeholder="Nombre o correo"
                    value={buscar}
                    onChange={(event) => setBuscar(event.target.value)}
                  />
                </div>
              </Field>
              <Field label="Rol" htmlFor="filtro-rol" className="w-44">
                <Select
                  id="filtro-rol"
                  value={filtroRol}
                  onChange={(event) => setFiltroRol(event.target.value as RolId | '')}
                >
                  <option value="">Todos</option>
                  {roles.map((rol) => (
                    <option key={rol.id} value={rol.id}>
                      {rol.nombre}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
          </div>
        </CardHeader>

        {cargando ? (
          <p className="p-8 text-center text-sm text-slate-500">Cargando usuarios…</p>
        ) : usuarios.length === 0 ? (
          <div className="p-10 text-center">
            <KeyRound size={24} aria-hidden="true" className="mx-auto mb-2 text-slate-300" />
            <p className="text-sm text-slate-500">
              No hay usuarios que coincidan con la búsqueda.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Usuarios, roles y estado de su cuenta</caption>
              <thead className="border-b border-border bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th scope="col" className="px-6 py-3 font-semibold">
                    Usuario
                  </th>
                  <th scope="col" className="px-6 py-3 font-semibold">
                    Departamento
                  </th>
                  <th scope="col" className="px-6 py-3 font-semibold">
                    Rol (RBAC)
                  </th>
                  <th scope="col" className="px-6 py-3 font-semibold">
                    Estado
                  </th>
                  <th scope="col" className="px-6 py-3 font-semibold">
                    Último acceso
                  </th>
                  {puedeAdministrar && (
                    <th scope="col" className="px-6 py-3 font-semibold">
                      Acciones
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usuarios.map((fila) => {
                  const estado = ESTADO_BADGE[fila.estado]
                  const esYo = fila.id === usuario.id
                  return (
                    <tr key={fila.id} className="transition-colors hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <p className="font-medium text-slate-800">{fila.nombre}</p>
                        <p className="text-xs text-slate-500">{fila.correo}</p>
                      </td>
                      <td className="px-6 py-4 text-slate-600">{fila.departamento ?? '—'}</td>
                      <td className="px-6 py-4">
                        {puedeAdministrar && !esYo ? (
                          <Select
                            aria-label={`Rol de ${fila.nombre}`}
                            className="h-9 w-44"
                            value={fila.rol}
                            onChange={(event) => {
                              const rol = event.target.value as RolId
                              void accion(
                                () => updateUser(fila.id, { rol }),
                                (u) => `${u.nombre} ahora es ${nombreRol(u.rol)}.`,
                              )
                            }}
                          >
                            {roles.map((rol) => (
                              <option key={rol.id} value={rol.id}>
                                {rol.nombre}
                              </option>
                            ))}
                          </Select>
                        ) : (
                          <Badge variant="default">{nombreRol(fila.rol)}</Badge>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={estado.variant}>{estado.label}</Badge>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {fechaCorta(fila.ultimo_acceso)}
                      </td>
                      {puedeAdministrar && (
                        <td className="px-6 py-4">
                          {esYo ? (
                            <span className="text-xs text-slate-400">Tu cuenta</span>
                          ) : fila.estado === 'bloqueado' ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                void accion(
                                  () => unlockUser(fila.id),
                                  (u) => `Cuenta de ${u.nombre} reactivada.`,
                                )
                              }
                            >
                              <Unlock size={16} aria-hidden="true" />
                              Desbloquear
                            </Button>
                          ) : fila.estado === 'suspendido' ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                void accion(
                                  () => updateUser(fila.id, { estado: 'activo' }),
                                  (u) => `Cuenta de ${u.nombre} reactivada.`,
                                )
                              }
                            >
                              <UserCheck size={16} aria-hidden="true" />
                              Reactivar
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                void accion(
                                  () => updateUser(fila.id, { estado: 'suspendido' }),
                                  (u) => `Cuenta de ${u.nombre} suspendida.`,
                                )
                              }
                            >
                              {fila.estado === 'invitado' ? (
                                <UserX size={16} aria-hidden="true" />
                              ) : (
                                <Lock size={16} aria-hidden="true" />
                              )}
                              Suspender
                            </Button>
                          )}
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
