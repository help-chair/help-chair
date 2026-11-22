import { CheckCircle2, Flame, Inbox, TrendingUp, type LucideIcon } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { Metrics } from './data'

interface MetricCard {
  label: string
  value: number
  detail: string
  icon: LucideIcon
  /** Color del número. */
  tone: string
  /** Fondo y color del icono. */
  iconTone: string
  detailTone?: string
}

/** Fila de indicadores; se recalcula sola con cada cambio en los tickets. */
export function MetricsRow({ metrics }: { metrics: Metrics }) {
  const cards: MetricCard[] = [
    {
      label: 'Tickets abiertos',
      value: metrics.open,
      detail:
        metrics.newLastHour === 1
          ? '1 nuevo en la última hora'
          : `${metrics.newLastHour} nuevos en la última hora`,
      icon: Inbox,
      tone: 'text-slate-900',
      iconTone: 'bg-blue-50 text-blue-700',
      detailTone: 'text-blue-700',
    },
    {
      label: 'Tickets cerrados',
      value: metrics.closedToday,
      detail: 'Resueltos hoy',
      icon: CheckCircle2,
      tone: 'text-emerald-700',
      iconTone: 'bg-emerald-50 text-emerald-700',
    },
    {
      label: 'Urgentes activos',
      value: metrics.urgentActive,
      detail: 'Requieren atención inmediata',
      icon: Flame,
      tone: 'text-red-700',
      iconTone: 'bg-red-50 text-red-700',
    },
    {
      label: 'Escalados',
      value: metrics.escalated,
      detail: `${metrics.atMaxLevel} en Nivel 3`,
      icon: TrendingUp,
      tone: 'text-amber-800',
      iconTone: 'bg-amber-50 text-amber-800',
    },
  ]

  return (
    <section
      aria-label="Indicadores de incidentes"
      className="grid grid-cols-1 gap-4 md:grid-cols-4"
    >
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <Card key={card.label} className="flex items-start justify-between gap-3 p-5">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase text-slate-500">{card.label}</p>
              <p className={cn('mt-1 text-2xl font-bold', card.tone)}>{card.value}</p>
              <p className={cn('mt-1 text-xs', card.detailTone ?? 'text-slate-500')}>
                {card.detail}
              </p>
            </div>
            <span className={cn('shrink-0 rounded-lg p-2.5', card.iconTone)}>
              <Icon size={20} aria-hidden="true" />
            </span>
          </Card>
        )
      })}
    </section>
  )
}
