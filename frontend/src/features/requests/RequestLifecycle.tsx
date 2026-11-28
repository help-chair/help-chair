import { Check, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { APPROVAL_STEP, getStatus } from './data'
import type { ApprovalStatus, RequestStatus } from './types'

interface RequestLifecycleProps {
  status: RequestStatus
  /** Con `no_requerida` se omite el paso de aprobación. */
  approvalStatus: ApprovalStatus
  className?: string
}

type StepState = 'done' | 'current' | 'pending'

interface Step {
  id: string
  label: string
  description: string
  icon: LucideIcon
  state: StepState
}

const SR_STATE_LABEL: Record<StepState, string> = {
  done: 'completado',
  current: 'paso actual',
  pending: 'pendiente',
}

/** Camino principal del contrato; reabierto y cancelado no son pasos sino desvíos. */
const MAIN_PATH: RequestStatus[] = ['nuevo', 'asignado', 'en_proceso', 'resuelto', 'cerrado']

function buildSteps(status: RequestStatus, approvalStatus: ApprovalStatus): Step[] {
  // Una petición reabierta vuelve a manos de soporte: se muestra en «Asignada».
  const position = status === 'reabierto' ? 1 : MAIN_PATH.indexOf(status)
  // Mientras sea nueva y su servicio exija aprobación, el paso actual es «Aprobación».
  const atApproval =
    status === 'nuevo' && (approvalStatus === 'pendiente' || approvalStatus === 'aprobado')

  const steps: Step[] = MAIN_PATH.map((id, index) => {
    const info = getStatus(id)
    const state: StepState =
      status === 'cerrado' || index < position || (atApproval && index === 0)
        ? 'done'
        : index === position
          ? 'current'
          : 'pending'
    const description =
      status === 'reabierto' && index === position
        ? getStatus('reabierto').description
        : info.description
    return { id, label: info.label, description, icon: info.icon, state }
  })

  if (approvalStatus !== 'no_requerida') {
    const approval: Step = {
      id: 'aprobacion',
      label: APPROVAL_STEP.label,
      icon: APPROVAL_STEP.icon,
      description:
        approvalStatus === 'aprobado'
          ? 'Ya está aprobada; soporte la asignará pronto.'
          : APPROVAL_STEP.description,
      state: atApproval ? 'current' : approvalStatus === 'aprobado' ? 'done' : 'pending',
    }
    steps.splice(1, 0, approval)
  }
  return steps
}

/** Línea de vida: Nueva → (Aprobación) → Asignada → En proceso → Resuelta → Cerrada. */
export function RequestLifecycle({ status, approvalStatus, className }: RequestLifecycleProps) {
  const steps = buildSteps(status, approvalStatus)

  return (
    <ol
      aria-label="Línea de vida de la petición"
      className={cn('flex flex-col gap-3 sm:flex-row sm:gap-0', className)}
    >
      {steps.map((step, index) => {
        const Icon = step.icon
        const next = steps[index + 1]
        return (
          <li
            key={step.id}
            aria-current={step.state === 'current' ? 'step' : undefined}
            className="relative flex items-center gap-3 sm:flex-1 sm:flex-col sm:gap-2 sm:text-center"
          >
            {next && (
              <span
                aria-hidden="true"
                className={cn(
                  'absolute top-4 left-1/2 ml-5 hidden h-0.5 w-[calc(100%-2.5rem)] rounded-full sm:block',
                  next.state === 'pending' ? 'bg-slate-200' : 'bg-itil-request',
                )}
              />
            )}
            <span
              aria-hidden="true"
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold',
                step.state === 'done' && 'border-itil-request bg-itil-request text-white',
                step.state === 'current' &&
                  'border-itil-request bg-white text-itil-request ring-4 ring-purple-100',
                step.state === 'pending' && 'border-slate-200 bg-white text-slate-400',
              )}
            >
              {step.state === 'done' ? (
                <Check size={16} />
              ) : step.state === 'current' ? (
                <Icon size={16} />
              ) : (
                index + 1
              )}
            </span>
            <span className="min-w-0">
              <span
                className={cn(
                  'block text-xs font-semibold',
                  step.state === 'pending' ? 'text-slate-400' : 'text-slate-800',
                )}
              >
                {step.label}
                <span className="sr-only"> ({SR_STATE_LABEL[step.state]})</span>
              </span>
              {step.state === 'current' && (
                <span className="block text-xs text-slate-500">{step.description}</span>
              )}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
