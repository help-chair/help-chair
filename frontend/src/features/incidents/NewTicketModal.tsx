import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Mail, Phone, Ticket as TicketIcon, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Field, Input, Select, Textarea } from '@/components/ui/form'
import { Modal } from '@/components/ui/modal'
import { cn } from '@/lib/utils'
import {
  CHANNEL_LABEL,
  IMPACT_OPTIONS,
  PRIORITY_OPTIONS,
  TONE_DOT,
  URGENCY_OPTIONS,
  findOption,
  type Option,
} from './data'
import { EvidenceDropzone } from './EvidenceDropzone'
import type { Channel, Impact, NewTicketInput, Priority, Urgency } from './types'

interface NewTicketModalProps {
  open: boolean
  onClose: () => void
  /** Registra el caso en el servicio; devuelve el mensaje de error o `null` si salió bien. */
  onCreate: (input: NewTicketInput) => Promise<string | null>
}

const MIN_DESCRIPTION_LENGTH = 10

const CHANNELS: { value: Channel; icon: LucideIcon }[] = [
  { value: 'email', icon: Mail },
  { value: 'telefono', icon: Phone },
]

type Errors = Partial<Record<'requesterId' | 'requesterName' | 'description' | 'evidence', string>>

function describedBy(id: string, hasMessage: boolean) {
  return hasMessage ? `${id}-description` : undefined
}

/** Modal «Abrir ticket»: registra el caso con los datos del solicitante. */
export function NewTicketModal({ open, onClose, onCreate }: NewTicketModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Abrir ticket"
      description="Registra el caso con los datos del solicitante"
      icon={<TicketIcon size={20} aria-hidden="true" />}
    >
      <NewTicketForm onCancel={onClose} onCreate={onCreate} />
    </Modal>
  )
}

function NewTicketForm({
  onCancel,
  onCreate,
}: {
  onCancel: () => void
  onCreate: (input: NewTicketInput) => Promise<string | null>
}) {
  const [requesterId, setRequesterId] = useState('')
  const [requesterName, setRequesterName] = useState('')
  const [channel, setChannel] = useState<Channel>('email')
  const [description, setDescription] = useState('')
  // Arrancan en el punto medio para no marcar todo como urgente por accidente.
  const [urgency, setUrgency] = useState<Urgency>('media')
  const [priority, setPriority] = useState<Priority>('media')
  const [impact, setImpact] = useState<Impact>('medio')
  const [evidence, setEvidence] = useState<File | null>(null)
  const [errors, setErrors] = useState<Errors>({})
  const [submitAttempts, setSubmitAttempts] = useState(0)
  const [sending, setSending] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const formRef = useRef<HTMLFormElement>(null)

  // Tras un envío con errores, lleva el foco al primer campo inválido.
  useEffect(() => {
    if (submitAttempts === 0) return
    formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
  }, [submitAttempts])

  function clearError(key: keyof Errors) {
    setErrors((current) => {
      if (!current[key]) return current
      const next = { ...current }
      delete next[key]
      return next
    })
  }

  function validate(): Errors {
    const found: Errors = {}
    if (!requesterId.trim()) found.requesterId = 'Escribe el ID del solicitante.'
    if (!requesterName.trim()) found.requesterName = 'Escribe el nombre del solicitante.'
    if (!description.trim()) {
      found.description = 'Describe la falla.'
    } else if (description.trim().length < MIN_DESCRIPTION_LENGTH) {
      found.description = `Agrega un poco más de detalle (mínimo ${MIN_DESCRIPTION_LENGTH} caracteres).`
    }
    if (errors.evidence) found.evidence = errors.evidence
    return found
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (sending) return
    const found = validate()
    setErrors(found)
    setSubmitError(null)
    if (Object.keys(found).length > 0) {
      setSubmitAttempts((count) => count + 1)
      return
    }
    setSending(true)
    const error = await onCreate({
      requesterId: requesterId.trim().toUpperCase(),
      requesterName: requesterName.trim(),
      channel,
      description: description.trim(),
      urgency,
      priority,
      impact,
      evidenceName: evidence?.name,
    })
    // Si salió bien, el modal se cierra; si no, se conserva lo capturado y se muestra el motivo.
    if (error) {
      setSubmitError(error)
      setSending(false)
    }
  }

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
      <div className="space-y-5 overflow-y-auto p-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            label="ID del solicitante"
            htmlFor="ticket-requester-id"
            required
            error={errors.requesterId}
          >
            <Input
              id="ticket-requester-id"
              data-autofocus
              placeholder="A-1024"
              autoComplete="off"
              value={requesterId}
              invalid={Boolean(errors.requesterId)}
              aria-describedby={describedBy('ticket-requester-id', Boolean(errors.requesterId))}
              onChange={(event) => {
                setRequesterId(event.target.value)
                clearError('requesterId')
              }}
            />
          </Field>
          <Field
            label="Nombre del solicitante"
            htmlFor="ticket-requester-name"
            required
            error={errors.requesterName}
          >
            <Input
              id="ticket-requester-name"
              placeholder="Nombre completo"
              autoComplete="name"
              value={requesterName}
              invalid={Boolean(errors.requesterName)}
              aria-describedby={describedBy('ticket-requester-name', Boolean(errors.requesterName))}
              onChange={(event) => {
                setRequesterName(event.target.value)
                clearError('requesterName')
              }}
            />
          </Field>
        </div>

        <fieldset className="space-y-1.5">
          <legend className="text-sm font-medium text-slate-700">Canal de ingreso</legend>
          <div className="grid grid-cols-2 gap-3">
            {CHANNELS.map(({ value, icon: Icon }) => (
              <label key={value} className="relative">
                <input
                  type="radio"
                  name="ticket-channel"
                  value={value}
                  checked={channel === value}
                  onChange={() => setChannel(value)}
                  className="peer sr-only"
                />
                <span className="flex h-10 cursor-pointer items-center justify-center gap-2 rounded-lg border border-border bg-white text-sm font-medium text-slate-700 transition-colors hover:bg-surface-muted peer-checked:border-primary peer-checked:bg-primary/5 peer-checked:text-primary peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-1">
                  <Icon size={16} aria-hidden="true" />
                  {CHANNEL_LABEL[value]}
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <Field
          label="Descripción breve de la falla"
          htmlFor="ticket-description"
          required
          error={errors.description}
        >
          <Textarea
            id="ticket-description"
            rows={3}
            placeholder="Describe qué falló y desde cuándo…"
            value={description}
            invalid={Boolean(errors.description)}
            aria-describedby={describedBy('ticket-description', Boolean(errors.description))}
            onChange={(event) => {
              setDescription(event.target.value)
              clearError('description')
            }}
          />
        </Field>

        <section aria-labelledby="ticket-categorizacion" className="space-y-3">
          <h3 id="ticket-categorizacion" className="text-sm font-semibold text-slate-800">
            Categorización
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <ToneSelect
              id="ticket-urgency"
              label="Urgencia"
              options={URGENCY_OPTIONS}
              value={urgency}
              onChange={setUrgency}
            />
            <ToneSelect
              id="ticket-priority"
              label="Prioridad"
              options={PRIORITY_OPTIONS}
              value={priority}
              onChange={setPriority}
            />
            <ToneSelect
              id="ticket-impact"
              label="Impacto"
              options={IMPACT_OPTIONS}
              value={impact}
              onChange={setImpact}
            />
          </div>
        </section>

        <EvidenceDropzone
          id="ticket-evidence"
          file={evidence}
          error={errors.evidence}
          onChange={(file, error) => {
            setEvidence(file)
            setErrors((current) => ({ ...current, evidence: error }))
          }}
        />
      </div>

      {submitError && (
        <p
          role="alert"
          className="mx-5 mb-0 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          No se pudo registrar el incidente: {submitError}
        </p>
      )}
      <div className="flex flex-col-reverse gap-3 border-t border-border/50 p-5 sm:flex-row sm:justify-end">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={sending}>
          {sending ? 'Registrando…' : 'Crear ticket'}
        </Button>
      </div>
    </form>
  )
}

/** Lista desplegable con el punto de color del valor elegido (como en el diseño). */
function ToneSelect<T extends string>({
  id,
  label,
  options,
  value,
  onChange,
}: {
  id: string
  label: string
  options: Option<T>[]
  value: T
  onChange: (value: T) => void
}) {
  const current = findOption(options, value)
  return (
    <Field label={label} htmlFor={id}>
      <div className="relative">
        <span
          aria-hidden="true"
          className={cn(
            'pointer-events-none absolute left-3 top-1/2 z-10 h-2 w-2 -translate-y-1/2 rounded-full',
            TONE_DOT[current.variant],
          )}
        />
        <Select
          id={id}
          value={value}
          className="pl-7"
          onChange={(event) => onChange(event.target.value as T)}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>
    </Field>
  )
}
