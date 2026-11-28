import { cn } from '@/lib/utils'
import { getRating, type SurveyAnswer } from './options'

interface SurveySummaryProps {
  answer: SurveyAnswer
  className?: string
}

/** Encuesta ya respondida, en modo de solo lectura. */
export function SurveySummary({ answer, className }: SurveySummaryProps) {
  const option = getRating(answer.rating)
  const Icon = option.icon
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border border-border bg-white p-4',
        className,
      )}
    >
      <span className={cn('rounded-lg border p-2', option.tone)} aria-hidden="true">
        <Icon size={20} />
      </span>
      <div className="min-w-0 space-y-0.5">
        <p className="text-sm text-slate-600">
          Calificaste la atención como{' '}
          <strong className="font-semibold text-slate-800">{option.label}</strong>{' '}
          <span className="text-xs text-slate-500">({answer.rating} de 5)</span>
        </p>
        {answer.comment && <p className="text-sm italic text-slate-600">«{answer.comment}»</p>}
      </div>
    </div>
  )
}
