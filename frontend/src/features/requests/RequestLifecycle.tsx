import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { REQUEST_STATES } from './data'
import type { RequestStatus } from './types'

interface RequestLifecycleProps {
  status: RequestStatus
  /** Si el servicio no requiere aprobación, se omite ese paso. */
  requiresApproval: boolean
  className?: string
}

type StepState = 'done' | 'current' | 'pending'

const SR_STATE_LABEL: Record<StepState, string> = {
  done: 'completado',
  current: 'paso actual',
  pending: 'pendiente',
}

/** Línea de vida de la petición: Enviada → Aprobación pendiente → En provisión → Completada. */
export function RequestLifecycle({ status, requiresApproval, className }: RequestLifecycleProps) {
  const steps = REQUEST_STATES.filter(
    (step) => requiresApproval || step.id !== 'aprobacion_pendiente',
  )
  const currentIndex = steps.findIndex((step) => step.id === status)

  return (
    <ol
      aria-label="Línea de vida de la petición"
      className={cn('flex flex-col gap-3 sm:flex-row sm:gap-0', className)}
    >
      {steps.map((step, index) => {
        const state: StepState =
          index < currentIndex || status === 'completada'
            ? 'done'
            : index === currentIndex
              ? 'current'
              : 'pending'
        const Icon = step.icon

        return (
          <li
            key={step.id}
            aria-current={state === 'current' ? 'step' : undefined}
            className="relative flex items-center gap-3 sm:flex-1 sm:flex-col sm:gap-2 sm:text-center"
          >
            {index < steps.length - 1 && (
              <span
                aria-hidden="true"
                className={cn(
                  'absolute top-4 left-1/2 ml-5 hidden h-0.5 w-[calc(100%-2.5rem)] rounded-full sm:block',
                  index < currentIndex || status === 'completada'
                    ? 'bg-itil-request'
                    : 'bg-slate-200',
                )}
              />
            )}
            <span
              aria-hidden="true"
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold',
                state === 'done' && 'border-itil-request bg-itil-request text-white',
                state === 'current' &&
                  'border-itil-request bg-white text-itil-request ring-4 ring-purple-100',
                state === 'pending' && 'border-slate-200 bg-white text-slate-400',
              )}
            >
              {state === 'done' ? (
                <Check size={16} />
              ) : state === 'current' ? (
                <Icon size={16} />
              ) : (
                index + 1
              )}
            </span>
            <span className="min-w-0">
              <span
                className={cn(
                  'block text-xs font-semibold',
                  state === 'pending' ? 'text-slate-400' : 'text-slate-800',
                )}
              >
                {step.label}
                <span className="sr-only"> ({SR_STATE_LABEL[state]})</span>
              </span>
              {state === 'current' && (
                <span className="block text-xs text-slate-500">{step.description}</span>
              )}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
