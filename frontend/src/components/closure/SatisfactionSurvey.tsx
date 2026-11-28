import { useId, useRef, useState, type FormEvent } from 'react'
import { AlertCircle, MessageSquareHeart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Field, Textarea } from '@/components/ui/form'
import { cn } from '@/lib/utils'
import { COMMENT_MAX_LENGTH, RATING_OPTIONS, type Rating, type SurveyInput } from './options'

interface SatisfactionSurveyProps {
  /** Qué se califica, para lectores de pantalla (ej. «REQ-0012 · Periféricos»). */
  subject: string
  /** Texto del botón principal, con el verbo de lo que pasa al enviarla. */
  submitLabel: string
  /** Puede devolver una promesa: mientras se resuelve, el botón muestra «Guardando…». */
  onSubmit: (input: SurveyInput) => void | Promise<void>
  /** Acción secundaria opcional (ej. reabrir si no quedó resuelta). */
  secondaryAction?: { label: string; onClick: () => void }
  className?: string
}

/**
 * Encuesta de satisfacción (CSAT) que ve el solicitante al resolverse o cerrarse su caso.
 * Escala de 1 a 5 con caras y comentario opcional. Maneja los estados de envío y de error.
 */
export function SatisfactionSurvey({
  subject,
  submitLabel,
  onSubmit,
  secondaryAction,
  className,
}: SatisfactionSurveyProps) {
  const id = useId()
  const titleId = `${id}-titulo`
  const ratingErrorId = `${id}-error`
  const commentId = `${id}-comentario`
  const firstOptionRef = useRef<HTMLInputElement>(null)

  const [rating, setRating] = useState<Rating | null>(null)
  const [comment, setComment] = useState('')
  const [showRatingError, setShowRatingError] = useState(false)
  const [status, setStatus] = useState<'idle' | 'saving' | 'error'>('idle')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (rating === null) {
      setShowRatingError(true)
      firstOptionRef.current?.focus()
      return
    }
    setStatus('saving')
    try {
      const text = comment.trim()
      await onSubmit(text ? { rating, comment: text } : { rating })
      setStatus('idle')
    } catch {
      setStatus('error')
    }
  }

  return (
    <form
      noValidate
      aria-labelledby={titleId}
      onSubmit={handleSubmit}
      className={cn('space-y-4 rounded-lg border border-purple-200 bg-white p-4', className)}
    >
      <div className="flex items-start gap-3">
        <span className="rounded-lg bg-purple-50 p-2 text-purple-700" aria-hidden="true">
          <MessageSquareHeart size={18} />
        </span>
        <div>
          <h5 id={titleId} className="text-sm font-semibold text-slate-800">
            ¿Cómo te atendimos?
            <span className="sr-only"> ({subject})</span>
          </h5>
          <p className="text-xs text-slate-600">
            Tu calificación ayuda al equipo de soporte a mejorar. Toma menos de un minuto.
          </p>
        </div>
      </div>

      <fieldset aria-describedby={showRatingError ? ratingErrorId : undefined}>
        <legend className="mb-2 text-sm font-medium text-slate-700">
          Califica la atención
          <span className="text-red-600" aria-hidden="true">
            {' '}
            *
          </span>
        </legend>
        <div className="grid grid-cols-5 gap-2">
          {RATING_OPTIONS.map((option, index) => {
            const Icon = option.icon
            return (
              <label key={option.value} className="relative cursor-pointer">
                <input
                  ref={index === 0 ? firstOptionRef : undefined}
                  type="radio"
                  name={`${id}-calificacion`}
                  value={option.value}
                  checked={rating === option.value}
                  onChange={() => {
                    setRating(option.value)
                    setShowRatingError(false)
                  }}
                  aria-invalid={showRatingError || undefined}
                  className="peer sr-only"
                />
                <span
                  className={cn(
                    'flex h-full flex-col items-center gap-1 rounded-lg border bg-white px-1 py-2.5 text-center text-xs font-medium text-slate-600 transition-colors',
                    'hover:shadow-sm',
                    'peer-checked:font-semibold peer-checked:ring-2 peer-checked:ring-current',
                    'peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ring',
                    showRatingError ? 'border-red-500' : 'border-border',
                    option.checked,
                  )}
                >
                  <Icon size={24} aria-hidden="true" />
                  {/* En pantallas angostas solo caben las caras: el texto queda para lectores. */}
                  <span className="sr-only sm:not-sr-only">{option.label}</span>
                </span>
              </label>
            )
          })}
        </div>
        <div
          aria-hidden="true"
          className="mt-1.5 flex justify-between text-xs text-slate-500 sm:hidden"
        >
          <span>{RATING_OPTIONS[0].label}</span>
          <span>{RATING_OPTIONS[RATING_OPTIONS.length - 1].label}</span>
        </div>
        {showRatingError && (
          <p id={ratingErrorId} role="alert" className="mt-1.5 text-xs font-medium text-red-700">
            Elige una calificación del 1 al 5.
          </p>
        )}
      </fieldset>

      <Field
        label="¿Quieres contarnos algo más?"
        htmlFor={commentId}
        hint={`Opcional · ${comment.length}/${COMMENT_MAX_LENGTH} caracteres.`}
      >
        <Textarea
          id={commentId}
          rows={2}
          maxLength={COMMENT_MAX_LENGTH}
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          aria-describedby={`${commentId}-description`}
          placeholder="Ej. Me lo entregaron antes de lo esperado."
        />
      </Field>

      {status === 'error' && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          <AlertCircle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
          <p>No pudimos guardar tu calificación. Revisa tu conexión e inténtalo de nuevo.</p>
        </div>
      )}

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
        {secondaryAction ? (
          <Button type="button" variant="ghost" size="sm" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </Button>
        ) : (
          <span aria-hidden="true" />
        )}
        <Button type="submit" size="sm" disabled={status === 'saving'}>
          {status === 'saving'
            ? 'Guardando…'
            : status === 'error'
              ? 'Intentar de nuevo'
              : submitLabel}
        </Button>
      </div>
    </form>
  )
}
