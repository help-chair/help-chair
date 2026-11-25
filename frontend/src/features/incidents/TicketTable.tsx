import { useState } from 'react'
import { CheckCircle2, ChevronsUp, Clock, Mail, Paperclip, Phone } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/form'
import { cn } from '@/lib/utils'
import {
  CHANNEL_LABEL,
  IMPACT_OPTIONS,
  LEVEL_TONE,
  PRIORITY_OPTIONS,
  STATUS_LABEL,
  TONE_DOT,
  URGENCY_OPTIONS,
  findOption,
  formatTime,
  type Option,
} from './data'
import type { EscalationLevel, Priority, Ticket, TicketStatus } from './types'

interface TicketTableProps {
  tickets: Ticket[]
  /** Ticket recién creado, para resaltarlo. */
  highlightId: string | null
  /** Ticket con una acción en curso: sus botones se desactivan hasta que responda el servicio. */
  busyId?: string | null
  onEscalate: (ticketId: string) => void
  onClose: (ticketId: string) => void
}

const COLUMNS = [
  'ID / Hora',
  'Solicitante',
  'Canal',
  'Descripción de la falla',
  'Urgencia',
  'Prioridad',
  'Impacto',
  'Estado',
  'Nivel',
  'Acción',
]

function CategoryBadge<T extends string>({ options, value }: { options: Option<T>[]; value: T }) {
  const option = findOption(options, value)
  return (
    <Badge variant={option.variant} className="whitespace-nowrap">
      {option.label}
    </Badge>
  )
}

function LevelIndicator({ level }: { level: EscalationLevel }) {
  return (
    <div className="space-y-1">
      <p className="whitespace-nowrap text-xs font-medium text-slate-700">Nivel {level}</p>
      <div className="flex gap-0.5" aria-hidden="true">
        {[1, 2, 3].map((step) => (
          <span
            key={step}
            className={cn(
              'h-1 w-4 rounded-full',
              step <= level ? LEVEL_TONE[level] : 'bg-slate-200',
            )}
          />
        ))}
      </div>
    </div>
  )
}

/** Tabla «Tickets de incidentes recientes» con filtros por estado y prioridad. */
export function TicketTable({
  tickets,
  highlightId,
  busyId = null,
  onEscalate,
  onClose,
}: TicketTableProps) {
  const [status, setStatus] = useState<TicketStatus | 'todos'>('todos')
  const [priority, setPriority] = useState<Priority | 'todas'>('todas')

  const visible = tickets.filter(
    (ticket) =>
      (status === 'todos' || ticket.status === status) &&
      (priority === 'todas' || ticket.priority === priority),
  )

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="text-base">Tickets de incidentes recientes</CardTitle>
          <CardDescription>
            Categorización, estado y nivel de escalamiento de cada caso
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Select
            aria-label="Filtrar por estado"
            value={status}
            className="h-8 w-44 text-xs"
            onChange={(event) => setStatus(event.target.value as TicketStatus | 'todos')}
          >
            <option value="todos">Estado: todos</option>
            <option value="abierto">Estado: abiertos</option>
            <option value="cerrado">Estado: cerrados</option>
          </Select>
          <Select
            aria-label="Filtrar por prioridad"
            value={priority}
            className="h-8 w-44 text-xs"
            onChange={(event) => setPriority(event.target.value as Priority | 'todas')}
          >
            <option value="todas">Prioridad: todas</option>
            {PRIORITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                Prioridad: {option.label.toLowerCase()}
              </option>
            ))}
          </Select>
        </div>
      </CardHeader>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[64rem] text-left text-sm">
          <caption className="sr-only">Tickets de incidentes recientes</caption>
          <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
            <tr>
              {COLUMNS.map((column) => (
                <th key={column} scope="col" className="whitespace-nowrap px-4 py-3">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {visible.map((ticket) => {
              const open = ticket.status === 'abierto'
              const ChannelIcon = ticket.channel === 'email' ? Mail : Phone
              return (
                <tr
                  key={ticket.id}
                  className={cn('align-top', ticket.id === highlightId && 'bg-primary/5')}
                >
                  <td className="px-4 py-3">
                    <p className="whitespace-nowrap font-mono text-xs font-bold text-slate-900">
                      {ticket.id}
                    </p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                      <Clock size={12} aria-hidden="true" />
                      <time dateTime={ticket.createdAt}>{formatTime(ticket.createdAt)}</time>
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="whitespace-nowrap font-medium text-slate-800">
                      {ticket.requesterName}
                    </p>
                    <p className="text-xs text-slate-500">{ticket.requesterId}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5 whitespace-nowrap text-slate-600">
                      <ChannelIcon size={16} aria-hidden="true" />
                      {CHANNEL_LABEL[ticket.channel]}
                    </span>
                  </td>
                  <td className="max-w-xs px-4 py-3">
                    <p className="text-slate-700">{ticket.description}</p>
                    {ticket.evidenceName && (
                      <p
                        className="mt-1 inline-flex items-center gap-1 text-xs text-slate-500"
                        title={ticket.evidenceName}
                      >
                        <Paperclip size={12} aria-hidden="true" />
                        Evidencia adjunta
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <CategoryBadge options={URGENCY_OPTIONS} value={ticket.urgency} />
                  </td>
                  <td className="px-4 py-3">
                    <CategoryBadge options={PRIORITY_OPTIONS} value={ticket.priority} />
                  </td>
                  <td className="px-4 py-3">
                    <CategoryBadge options={IMPACT_OPTIONS} value={ticket.impact} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="whitespace-nowrap bg-white text-slate-700">
                      <span
                        className={cn(
                          'h-1.5 w-1.5 rounded-full',
                          open ? TONE_DOT.info : TONE_DOT.default,
                        )}
                        aria-hidden="true"
                      />
                      {STATUS_LABEL[ticket.status]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <LevelIndicator level={ticket.level} />
                  </td>
                  <td className="px-4 py-3">
                    {open ? (
                      <div className="flex items-center gap-2">
                        {ticket.level < 3 ? (
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-red-200 text-red-700 hover:bg-red-50"
                            aria-label={`Escalar ${ticket.id}`}
                            disabled={busyId === ticket.id}
                            onClick={() => onEscalate(ticket.id)}
                          >
                            <ChevronsUp size={16} aria-hidden="true" />
                            Escalar
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled
                            title="El caso ya está en el nivel más alto"
                          >
                            Nivel máx.
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          aria-label={`Cerrar ${ticket.id}`}
                          disabled={busyId === ticket.id}
                          onClick={() => onClose(ticket.id)}
                        >
                          Cerrar
                        </Button>
                      </div>
                    ) : (
                      <span className="inline-flex items-center gap-1 whitespace-nowrap text-xs font-medium text-emerald-700">
                        <CheckCircle2 size={16} aria-hidden="true" />
                        Resuelto
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
            {visible.length === 0 && (
              <tr>
                <td
                  colSpan={COLUMNS.length}
                  className="px-4 py-10 text-center text-sm text-slate-500"
                >
                  No hay tickets con estos filtros.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
