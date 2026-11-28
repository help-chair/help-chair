import { useState, type ReactNode } from 'react'
import {
  Ban,
  Building2,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Paperclip,
  User,
  XCircle,
  type LucideIcon,
} from 'lucide-react'
import { CancelReasonDialog } from '@/components/closure/CancelReasonDialog'
import { SatisfactionSurvey } from '@/components/closure/SatisfactionSurvey'
import { SurveySummary } from '@/components/closure/SurveySummary'
import type { SurveyInput } from '@/components/closure/options'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import {
  APPROVAL_BADGE,
  canAnswerSurvey,
  formatDate,
  getCategory,
  getStatus,
  isActive,
} from './data'
import { RequestLifecycle } from './RequestLifecycle'
import type { ServiceRequest } from './types'

interface RequestListProps {
  requests: ServiceRequest[]
  /** Petición recién creada, para resaltarla. */
  highlightId?: string | null
  /** Confirmación de la última acción, que se muestra dentro de su tarjeta. */
  notice?: { requestId: string; message: string } | null
  onGoToCatalog: () => void
  onAnswerSurvey: (requestId: string, input: SurveyInput) => void | Promise<void>
  onReopen: (requestId: string) => void
  onCancel: (requestId: string, reason: string) => void | Promise<void>
}

/** Listado de peticiones del solicitante: estado, línea de vida y acciones de cierre. */
export function RequestList({
  requests,
  highlightId,
  notice,
  onGoToCatalog,
  onAnswerSurvey,
  onReopen,
  onCancel,
}: RequestListProps) {
  const [cancelling, setCancelling] = useState<ServiceRequest | null>(null)

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
          Sigue el avance de cada petición y califica la atención cuando se resuelva.
        </p>
      </div>

      <ul className="space-y-4">
        {requests.map((request) => {
          const status = getStatus(request.status)
          const category = getCategory(request.category)
          const approval = APPROVAL_BADGE[request.approvalStatus]
          const isNew = request.id === highlightId
          const subject = `${request.id} · ${request.serviceName}`
          const rejected = request.approvalStatus === 'rechazado'
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
                  <div className="flex shrink-0 flex-wrap gap-2 sm:justify-end">
                    {approval && <Badge variant={approval.variant}>{approval.label}</Badge>}
                    <Badge variant={status.badge}>{status.label}</Badge>
                  </div>
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

                {request.status === 'cancelado' ? (
                  <ClosedNote icon={Ban} title="Cancelaste esta petición">
                    {request.cancelReason && <>Motivo: {request.cancelReason}</>}
                  </ClosedNote>
                ) : rejected ? (
                  <ClosedNote
                    icon={XCircle}
                    title="El responsable no aprobó esta petición"
                    tone="exception"
                  >
                    {request.rejectionReason && <>Motivo: {request.rejectionReason}</>}
                  </ClosedNote>
                ) : (
                  <div className="mt-5 space-y-4 rounded-lg bg-slate-50 p-4">
                    <RequestLifecycle
                      status={request.status}
                      approvalStatus={request.approvalStatus}
                    />
                    {canAnswerSurvey(request) && (
                      <SatisfactionSurvey
                        subject={subject}
                        submitLabel={
                          request.status === 'resuelto'
                            ? 'Calificar y cerrar petición'
                            : 'Guardar calificación'
                        }
                        onSubmit={(input) => onAnswerSurvey(request.id, input)}
                        secondaryAction={
                          request.status === 'resuelto'
                            ? {
                                label: 'No quedó resuelta: reabrir',
                                onClick: () => onReopen(request.id),
                              }
                            : undefined
                        }
                      />
                    )}
                    {request.survey && <SurveySummary answer={request.survey} />}
                  </div>
                )}

                {notice?.requestId === request.id && (
                  <p
                    role="status"
                    className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"
                  >
                    <CheckCircle2 size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
                    {notice.message}
                  </p>
                )}

                {isActive(request) && (
                  <div className="mt-4 flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setCancelling(request)}
                      aria-describedby={`${request.id}-titulo`}
                    >
                      <Ban size={14} aria-hidden="true" />
                      Cancelar petición
                    </Button>
                  </div>
                )}
              </Card>
            </li>
          )
        })}
      </ul>

      <CancelReasonDialog
        open={cancelling !== null}
        subject={cancelling ? `${cancelling.id} · ${cancelling.serviceName}` : ''}
        onClose={() => setCancelling(null)}
        onConfirm={async (reason) => {
          if (!cancelling) return
          await onCancel(cancelling.id, reason)
          setCancelling(null)
        }}
      />
    </section>
  )
}

interface ClosedNoteProps {
  icon: LucideIcon
  title: string
  tone?: 'default' | 'exception'
  children?: ReactNode
}

/** Aviso que sustituye a la línea de vida cuando la petición ya no sigue el flujo. */
function ClosedNote({ icon: Icon, title, tone = 'default', children }: ClosedNoteProps) {
  return (
    <div
      className={cn(
        'mt-5 flex items-start gap-3 rounded-lg border p-4 text-sm',
        tone === 'exception'
          ? 'border-red-200 bg-red-50 text-red-700'
          : 'border-border bg-slate-50 text-slate-600',
      )}
    >
      <Icon size={18} aria-hidden="true" className="mt-0.5 shrink-0" />
      <div>
        <p className="font-semibold">{title}</p>
        {children && <p>{children}</p>}
      </div>
    </div>
  )
}
