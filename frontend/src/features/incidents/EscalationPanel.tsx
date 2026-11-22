import { Bell, Phone, PhoneCall } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { CALL_TARGET, formatElapsed } from './data'
import type { Escalation } from './types'

interface EscalationPanelProps {
  escalations: Escalation[]
  now: number
  onMarkCalled: (escalation: Escalation) => void
}

/** Casos que un nivel no pudo resolver: Incidentes debe llamar a alguien de mayor cargo. */
export function EscalationPanel({ escalations, now, onMarkCalled }: EscalationPanelProps) {
  const pending = escalations.filter((escalation) => !escalation.calledAt).length

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="text-base">Escalamientos a Incidentes</CardTitle>
          <CardDescription>
            Casos que un nivel no pudo resolver: Incidentes debe llamar a alguien de mayor cargo
          </CardDescription>
        </div>
        <Badge variant={pending > 0 ? 'warning' : 'success'} className="whitespace-nowrap">
          <Bell size={16} aria-hidden="true" />
          {pending === 1 ? '1 pendiente de llamada' : `${pending} pendientes de llamada`}
        </Badge>
      </CardHeader>

      {escalations.length === 0 ? (
        <p className="px-6 py-8 text-center text-sm text-slate-500">
          No hay escalamientos por ahora.
        </p>
      ) : (
        <ul aria-label="Escalamientos" className="divide-y divide-border">
          {escalations.map((escalation) => (
            <li
              key={escalation.id}
              className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center"
            >
              <span
                className={cn(
                  'w-fit shrink-0 rounded-lg p-2',
                  escalation.level === 3 ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-800',
                )}
              >
                <Bell size={16} aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-800">
                  {`${escalation.ticketId} escalado a Nivel ${escalation.level}`}
                </p>
                <p className="text-xs text-slate-500">
                  Incidentes debe llamar {CALL_TARGET[escalation.level]} ·{' '}
                  {formatElapsed(escalation.escalatedAt, now)}
                </p>
              </div>
              {escalation.calledAt ? (
                <Badge variant="success" className="w-fit whitespace-nowrap">
                  <PhoneCall size={16} aria-hidden="true" />
                  Llamada realizada
                </Badge>
              ) : (
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="warning" className="whitespace-nowrap">
                    Pendiente de llamada
                  </Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    aria-label={`Marcar como llamado ${escalation.ticketId} (Nivel ${escalation.level})`}
                    onClick={() => onMarkCalled(escalation)}
                  >
                    <Phone size={16} aria-hidden="true" />
                    Marcar como llamado
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
