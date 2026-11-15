import { Building2, CalendarDays, ClipboardList, Paperclip, User } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { STATUS_BADGE, formatDate, getCategory, getStatus } from './data'
import { RequestLifecycle } from './RequestLifecycle'
import type { ServiceRequest } from './types'

interface RequestListProps {
  requests: ServiceRequest[]
  /** Petición recién creada, para resaltarla. */
  highlightId?: string | null
  onGoToCatalog: () => void
}

/** Listado de peticiones registradas con su estado y su línea de vida. */
export function RequestList({ requests, highlightId, onGoToCatalog }: RequestListProps) {
  if (requests.length === 0) {
    return (
      <Card className="flex flex-col items-center gap-3 p-10 text-center">
        <ClipboardList size={24} className="text-slate-400" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold text-slate-800">Aún no tienes peticiones</p>
          <p className="text-sm text-slate-600">Cuando solicites un servicio, aparecerá aquí.</p>
        </div>
        <Button size="sm" onClick={onGoToCatalog}>
          Ir al catálogo
        </Button>
      </Card>
    )
  }

  return (
    <section aria-labelledby="mis-peticiones-titulo" className="space-y-4">
      <div>
        <h3 id="mis-peticiones-titulo" className="text-base font-semibold text-slate-800">
          Mis peticiones
        </h3>
        <p className="text-sm text-slate-600">
          Sigue el avance de cada petición, desde que la envías hasta que se completa.
        </p>
      </div>

      <ul className="space-y-4">
        {requests.map((request) => {
          const status = getStatus(request.status)
          const category = getCategory(request.category)
          const isNew = request.id === highlightId
          return (
            <li key={request.id}>
              <Card className={cn('p-5', isNew && 'border-purple-200 ring-2 ring-purple-100')}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-500">
                        {request.id}
                      </span>
                      <span className="text-xs font-medium text-slate-400">{category.label}</span>
                      {isNew && <Badge variant="request">Nueva</Badge>}
                    </div>
                    <h4
                      id={`${request.id}-titulo`}
                      className="text-base font-semibold text-slate-800"
                    >
                      {request.serviceName}
                    </h4>
                    <p className="text-sm text-slate-600">{request.description}</p>
                  </div>
                  <Badge variant={STATUS_BADGE[request.status]} className="w-fit shrink-0">
                    {status.label}
                  </Badge>
                </div>

                <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <dt>
                      <CalendarDays size={14} aria-hidden="true" />
                      <span className="sr-only">Fecha de registro</span>
                    </dt>
                    <dd>{formatDate(request.createdAt)}</dd>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <dt>
                      <User size={14} aria-hidden="true" />
                      <span className="sr-only">Solicitante</span>
                    </dt>
                    <dd>{request.requester}</dd>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <dt>
                      <Building2 size={14} aria-hidden="true" />
                      <span className="sr-only">Departamento</span>
                    </dt>
                    <dd>{request.department}</dd>
                  </div>
                  {request.attachmentName && (
                    <div className="flex items-center gap-1.5">
                      <dt>
                        <Paperclip size={14} aria-hidden="true" />
                        <span className="sr-only">Archivo adjunto</span>
                      </dt>
                      <dd>{request.attachmentName}</dd>
                    </div>
                  )}
                </dl>

                <div className="mt-5 rounded-lg bg-slate-50 p-4">
                  <RequestLifecycle
                    status={request.status}
                    requiresApproval={request.requiresApproval}
                  />
                </div>
              </Card>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
