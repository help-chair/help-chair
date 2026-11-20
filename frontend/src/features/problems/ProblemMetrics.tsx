import { Link2, Repeat, ShieldAlert, Wrench, type LucideIcon } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { estaAbierto } from './data'
import type { ErrorConocido, Problema, ProblemaIncidente } from './types'

interface ProblemMetricsProps {
  problemas: Problema[]
  incidentes: ProblemaIncidente[]
  errores: ErrorConocido[]
}

interface Indicador {
  label: string
  value: number
  detail: string
  icon: LucideIcon
  tone: string
  iconTone: string
  detailTone?: string
}

/** Fila de indicadores; se recalcula sola con cada cambio. */
export function ProblemMetrics({ problemas, incidentes, errores }: ProblemMetricsProps) {
  const abiertos = problemas.filter(estaAbierto)
  const criticos = abiertos.filter((problema) => problema.prioridad === 'critica').length
  const conIncidencias = new Set(incidentes.map((vinculo) => vinculo.problema_id)).size

  const indicadores: Indicador[] = [
    {
      label: 'Problemas abiertos',
      value: abiertos.length,
      detail: criticos === 1 ? '1 con prioridad crítica' : `${criticos} con prioridad crítica`,
      icon: ShieldAlert,
      tone: 'text-slate-900',
      iconTone: 'bg-amber-50 text-amber-800',
      detailTone: 'text-red-700',
    },
    {
      label: 'Detectados por patrón',
      value: problemas.filter((problema) => problema.origen === 'patron').length,
      detail: 'A partir de incidencias repetidas',
      icon: Repeat,
      tone: 'text-blue-700',
      iconTone: 'bg-blue-50 text-blue-700',
    },
    {
      label: 'Errores conocidos',
      value: errores.filter((error) => error.activo).length,
      detail: 'Activos, con solución temporal',
      icon: Wrench,
      tone: 'text-amber-800',
      iconTone: 'bg-amber-50 text-amber-800',
    },
    {
      label: 'Incidencias vinculadas',
      value: incidentes.length,
      detail: conIncidencias === 1 ? 'En 1 problema' : `Repartidas en ${conIncidencias} problemas`,
      icon: Link2,
      tone: 'text-red-700',
      iconTone: 'bg-red-50 text-red-700',
    },
  ]

  return (
    <section
      aria-label="Indicadores de problemas"
      className="grid grid-cols-1 gap-4 md:grid-cols-4"
    >
      {indicadores.map((indicador) => {
        const Icon = indicador.icon
        return (
          <Card key={indicador.label} className="flex items-start justify-between gap-3 p-5">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase text-slate-500">{indicador.label}</p>
              <p className={cn('mt-1 text-2xl font-bold', indicador.tone)}>{indicador.value}</p>
              <p className={cn('mt-1 text-xs', indicador.detailTone ?? 'text-slate-500')}>
                {indicador.detail}
              </p>
            </div>
            <span className={cn('shrink-0 rounded-lg p-2.5', indicador.iconTone)}>
              <Icon size={20} aria-hidden="true" />
            </span>
          </Card>
        )
      })}
    </section>
  )
}
