import { useId, useRef, useState, type FormEvent } from 'react'
import { AlertCircle, Ban } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Field, Textarea } from '@/components/ui/form'
import { Modal } from '@/components/ui/modal'
import { cn } from '@/lib/utils'
import { CANCEL_REASONS, OTHER_REASON, buildCancelReason, type CancelReason } from './options'

const DETAIL_MAX_LENGTH = 200

interface CancelReasonDialogProps {
  open: boolean
  /** Qué se cancela (ej. «REQ-0014 · Instalación de programa»). */
  subject: string
  onClose: () => void
  /** Recibe el motivo ya armado (máx. 255 caracteres). Puede devolver una promesa. */
  onConfirm: (reason: string) => void | Promise<void>
}

/**
 * Pide el motivo antes de cancelar. ITIL v4 lo registra para entender por qué
 * se abandonan las peticiones (y mejorar el catálogo o los tiempos de entrega).
 */
export function CancelReasonDialog({ open, subject, onClose, onConfirm }: CancelReasonDialogProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Cancelar petición"
      description={`${subject}. Al cancelarla, soporte deja de trabajar en ella.`}
      icon={<Ban size={20} />}
    >
      {/* Se monta de nuevo en cada apertura para empezar sin respuestas previas. */}
      {open && <CancelReasonForm onClose={onClose} onConfirm={onConfirm} />}
    </Modal>
  )
}

function CancelReasonForm({
  onClose,
  onConfirm,
}: Pick<CancelReasonDialogProps, 'onClose' | 'onConfirm'>) {
  const id = useId()
  const reasonErrorId = `${id}-motivo-error`
  const detailId = `${id}-detalle`
  const firstOptionRef = useRef<HTMLInputElement>(null)
  const detailRef = useRef<HTMLTextAreaElement>(null)

  const [reason, setReason] = useState<CancelReason | null>(null)
  const [detail, setDetail] = useState('')
  const [errors, setErrors] = useState<{ reason?: string; detail?: string }>({})
  const [status, setStatus] = useState<'idle' | 'saving' | 'error'>('idle')

  const needsDetail = reason === OTHER_REASON

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (reason === null) {
      setErrors({ reason: 'Elige un motivo.' })
      firstOptionRef.current?.focus()
      return
    }
    if (needsDetail && !detail.trim()) {
      setErrors({ detail: 'Escribe el motivo de la cancelación.' })
      detailRef.current?.focus()
      return
    }
    setErrors({})
    setStatus('saving')
    try {
      await onConfirm(buildCancelReason(reason, detail))
    } catch {
      setStatus('error')
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
      <div className="space-y-4 overflow-y-auto p-5">
        <fieldset aria-describedby={errors.reason ? reasonErrorId : undefined}>
          <legend className="mb-2 text-sm font-medium text-slate-700">
            ¿Por qué la cancelas?
            <span className="text-red-600" aria-hidden="true">
              {' '}
              *
            </span>
          </legend>
          <div className="space-y-2">
            {CANCEL_REASONS.map((option, index) => (
              <label
                key={option}
                className={cn(
                  'flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm text-slate-700 transition-colors has-[:checked]:border-primary has-[:checked]:bg-slate-50 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring',
                  errors.reason ? 'border-red-500' : 'border-border',
                )}
              >
                <input
                  ref={index === 0 ? firstOptionRef : undefined}
                  type="radio"
                  name={`${id}-motivo`}
                  value={option}
                  checked={reason === option}
                  onChange={() => {
                    setReason(option)
                    setErrors({})
                  }}
                  aria-invalid={Boolean(errors.reason) || undefined}
                  className="h-4 w-4 accent-primary focus-visible:outline-none"
                />
                {option}
              </label>
            ))}
          </div>
          {errors.reason && (
            <p id={reasonErrorId} role="alert" className="mt-1.5 text-xs font-medium text-red-700">
              {errors.reason}
            </p>
          )}
        </fieldset>

        <Field
          label={needsDetail ? 'Cuéntanos el motivo' : 'Detalles'}
          htmlFor={detailId}
          required={needsDetail}
          error={errors.detail}
          hint={needsDetail ? undefined : 'Opcional.'}
        >
          <Textarea
            ref={detailRef}
            id={detailId}
            rows={3}
            maxLength={DETAIL_MAX_LENGTH}
            value={detail}
            onChange={(event) => {
              setDetail(event.target.value)
              if (errors.detail) setErrors({})
            }}
            invalid={Boolean(errors.detail)}
            aria-describedby={errors.detail || !needsDetail ? `${detailId}-description` : undefined}
            placeholder="Ej. Me prestaron un equipo en el área."
          />
        </Field>

        {status === 'error' && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          >
            <AlertCircle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
            <p>No pudimos cancelar la petición. Revisa tu conexión e inténtalo de nuevo.</p>
          </div>
        )}
      </div>

      <div className="flex flex-col-reverse gap-3 border-t border-border/50 p-5 sm:flex-row sm:justify-end">
        <Button type="button" variant="outline" onClick={onClose}>
          Conservar petición
        </Button>
        <Button type="submit" variant="danger" disabled={status === 'saving'}>
          {status === 'saving' ? 'Cancelando…' : 'Cancelar petición'}
        </Button>
      </div>
    </form>
  )
}
