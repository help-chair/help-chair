import { ArrowLeft, BookOpen, Link2, Target, Unlink, Wrench } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ANALISTAS,
  AVANCES,
  INCIDENCIAS,
  codigoError,
  codigoProblema,
  formatFecha,
  siguienteEstado,
} from './data'
import { EstadoBadge, OrigenEtiqueta, PrioridadBadge } from './ProblemBadges'
import { ProblemLifecycle } from './ProblemLifecycle'
import type { ErrorConocido, PorQue, Problema, ProblemaIncidente } from './types'

interface ProblemDetailProps {
  problema: Problema
  incidentes: ProblemaIncidente[]
  errorConocido?: ErrorConocido
  analisis?: PorQue[]
  onVolver: () => void
  onAvanzar: () => void
  onVincular: () => void
  onDesvincular: (incidenteId: string) => void
}

/** Detalle de un problema: ciclo de vida, análisis de causa raíz, incidencias y error conocido. */
export function ProblemDetail({
  problema,
  incidentes,
  errorConocido,
  analisis,
  onVolver,
  onAvanzar,
  onVincular,
  onDesvincular,
}: ProblemDetailProps) {
  const codigo = codigoProblema(problema.id)
  const destino = siguienteEstado(problema.estado)
  const analista = ANALISTAS[problema.asignado_a_id]
  const cerrado = problema.estado === 'cerrado'

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" className="-ml-3 text-primary" onClick={onVolver}>
        <ArrowLeft size={16} aria-hidden="true" />
        Volver a Problemas
      </Button>

      <Card className="flex flex-col gap-4 p-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-xs font-bold text-slate-900">
              {codigo}
            </span>
            <PrioridadBadge prioridad={problema.prioridad} />
            <EstadoBadge estado={problema.estado} />
            <OrigenEtiqueta origen={problema.origen} />
          </div>
          <h3 className="text-xl font-bold text-slate-900">{problema.titulo}</h3>
          <p className="text-xs text-slate-500">
            Registrado el {formatFecha(problema.creado_en)} · Actualizado el{' '}
            {formatFecha(problema.actualizado_en)} ·{' '}
            {analista ? `Asignado a ${analista}` : 'Sin asignar'}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button variant="outline" onClick={onVincular} disabled={cerrado}>
            <Link2 size={16} aria-hidden="true" />
            Vincular incidencia
          </Button>
          {destino && (
            <Button variant="primary" onClick={onAvanzar}>
              {AVANCES[destino as keyof typeof AVANCES].boton}
            </Button>
          )}
        </div>
      </Card>

      <Card className="p-6">
        <h4 className="mb-4 text-sm font-semibold text-slate-800">Ciclo de vida del problema</h4>
        <ProblemLifecycle estado={problema.estado} />
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Descripción</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="max-w-prose text-sm text-slate-600">{problema.descripcion}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Análisis de causa raíz · 5 porqués</CardTitle>
              <CardDescription>
                Cada respuesta se vuelve la siguiente pregunta hasta llegar al origen
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analisis && analisis.length > 0 ? (
                <ol className="max-w-prose space-y-4">
                  {analisis.map((paso, indice) => (
                    <li key={paso.pregunta} className="flex gap-3">
                      <span
                        aria-hidden="true"
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-bold text-indigo-700"
                      >
                        {indice + 1}
                      </span>
                      <div className="text-sm">
                        <p className="font-semibold text-slate-800">{paso.pregunta}</p>
                        <p className="mt-0.5 text-slate-600">{paso.respuesta}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-slate-500">Todavía no hay un análisis de 5 porqués.</p>
              )}
              {problema.causa_raiz ? (
                <div className="flex gap-3 rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                  <Target size={20} aria-hidden="true" className="shrink-0 text-indigo-700" />
                  <div className="max-w-prose">
                    <p className="text-xs font-semibold uppercase text-indigo-700">Causa raíz</p>
                    <p className="mt-1 text-sm font-medium text-slate-800">{problema.causa_raiz}</p>
                  </div>
                </div>
              ) : (
                <p className="rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500">
                  La causa raíz aún no se identifica.
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="overflow-hidden">
            <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 space-y-0">
              <div className="space-y-1.5">
                <CardTitle className="text-base">Incidencias vinculadas</CardTitle>
                <CardDescription>
                  Incidencias del módulo de Incidencias con esta causa
                </CardDescription>
              </div>
              <Badge variant="exception">{incidentes.length} vinculadas</Badge>
            </CardHeader>
            {incidentes.length === 0 ? (
              <div className="flex flex-col items-center p-8 text-center">
                <Link2 size={40} aria-hidden="true" className="mb-2 text-slate-400" />
                <p className="text-base font-semibold text-slate-800">Sin incidencias vinculadas</p>
                <p className="mb-4 text-sm text-slate-500">
                  Vincula las incidencias que comparten esta causa para medir su impacto.
                </p>
                <Button variant="primary" size="sm" onClick={onVincular} disabled={cerrado}>
                  Vincular incidencia
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-left text-sm">
                  <caption className="sr-only">Incidencias vinculadas a {codigo}</caption>
                  <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
                    <tr>
                      <th scope="col" className="px-4 py-3">
                        ID
                      </th>
                      <th scope="col" className="px-4 py-3">
                        Descripción de la falla
                      </th>
                      <th scope="col" className="px-4 py-3">
                        Vinculada
                      </th>
                      <th scope="col" className="px-4 py-3">
                        Acción
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {incidentes.map((vinculo) => (
                      <tr key={vinculo.id}>
                        <td className="whitespace-nowrap px-4 py-3 font-mono text-xs font-bold text-slate-900">
                          {vinculo.incidente_id}
                        </td>
                        <td className="px-4 py-3 text-slate-700">
                          {INCIDENCIAS[vinculo.incidente_id] ?? (
                            <span className="text-slate-500">
                              Detalle en el módulo de Incidencias
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-slate-500">
                          <time dateTime={vinculo.vinculado_en}>
                            {formatFecha(vinculo.vinculado_en)}
                          </time>
                        </td>
                        <td className="px-4 py-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            aria-label={`Desvincular ${vinculo.incidente_id}`}
                            disabled={cerrado}
                            onClick={() => onDesvincular(vinculo.incidente_id)}
                          >
                            <Unlink size={16} aria-hidden="true" />
                            Desvincular
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card className={errorConocido?.activo ? 'border-t-4 border-t-itil-warning' : undefined}>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">Error conocido</CardTitle>
              {errorConocido && (
                <Badge variant={errorConocido.activo ? 'warning' : 'outline'}>
                  {codigoError(errorConocido.id)}
                  {!errorConocido.activo && ' · Retirado'}
                </Badge>
              )}
            </CardHeader>
            <CardContent className="space-y-3">
              {errorConocido ? (
                <>
                  <p className="flex items-center gap-1.5 text-xs font-semibold uppercase text-amber-800">
                    <Wrench size={14} aria-hidden="true" />
                    Solución temporal (workaround)
                  </p>
                  <p className="text-sm text-slate-700">{errorConocido.workaround}</p>
                  {errorConocido.articulo_kb_id && (
                    <p className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                      <BookOpen size={16} aria-hidden="true" />
                      Artículo {errorConocido.articulo_kb_id} en la Base de Conocimiento
                    </p>
                  )}
                  <p className="text-xs text-slate-500">
                    Publicado el {formatFecha(errorConocido.creado_en)}
                  </p>
                </>
              ) : (
                <p className="text-sm text-slate-500">
                  Todavía no hay error conocido. Se publica después de identificar la causa raíz.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Detalles</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2.5 text-sm">
                <dt className="text-slate-500">Prioridad</dt>
                <dd>
                  <PrioridadBadge prioridad={problema.prioridad} />
                </dd>
                <dt className="text-slate-500">Origen</dt>
                <dd>
                  <OrigenEtiqueta origen={problema.origen} />
                </dd>
                <dt className="text-slate-500">Asignado a</dt>
                <dd className="text-slate-800">{analista ?? 'Sin asignar'}</dd>
                <dt className="text-slate-500">Registrado</dt>
                <dd className="text-slate-800">{formatFecha(problema.creado_en)}</dd>
                {problema.resuelto_en && (
                  <>
                    <dt className="text-slate-500">Resuelto</dt>
                    <dd className="text-slate-800">{formatFecha(problema.resuelto_en)}</dd>
                  </>
                )}
              </dl>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
