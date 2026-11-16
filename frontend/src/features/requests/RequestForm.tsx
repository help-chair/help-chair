import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowLeft, Clock, Paperclip, Send, ShieldCheck, X, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader } from '@/components/ui/card'
import { Field, Input, Select, Textarea } from '@/components/ui/form'
import { DEPARTMENTS, formatDate, getCategory } from './data'
import type { CatalogService, NewRequestInput } from './types'

interface RequestFormProps {
  service: CatalogService
  onCancel: () => void
  onSubmit: (input: NewRequestInput) => void
}

const MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
const MIN_DESCRIPTION_LENGTH = 10

type Errors = Record<string, string>

function describedBy(id: string, hasMessage: boolean) {
  return hasMessage ? `${id}-description` : undefined
}

/** Formulario de solicitud: datos del solicitante + campos propios del servicio elegido. */
export function RequestForm({ service, onCancel, onSubmit }: RequestFormProps) {
  const [requester, setRequester] = useState('')
  const [department, setDepartment] = useState('')
  const [description, setDescription] = useState('')
  const [details, setDetails] = useState<Record<string, string>>({})
  const [attachment, setAttachment] = useState<File | null>(null)
  const [errors, setErrors] = useState<Errors>({})
  const [submitAttempts, setSubmitAttempts] = useState(0)
  const formRef = useRef<HTMLFormElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const category = getCategory(service.category)
  const CategoryIcon = category.icon
  const today = formatDate(new Date())

  // Tras un envío con errores, lleva el foco al primer campo inválido.
  useEffect(() => {
    if (submitAttempts === 0) return
    formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
  }, [submitAttempts])

  function clearError(key: string) {
    if (!errors[key]) return
    setErrors((current) => {
      const next = { ...current }
      delete next[key]
      return next
    })
  }

  function validate(): Errors {
    const found: Errors = {}
    if (!requester.trim()) found.requester = 'Escribe tu nombre completo.'
    if (!department) found.department = 'Elige tu departamento.'
    for (const field of service.extraFields) {
      if (field.required && !details[field.id]?.trim()) {
        found[`extra-${field.id}`] = `Completa el campo «${field.label}».`
      }
    }
    if (!description.trim()) {
      found.description = 'Describe lo que necesitas.'
    } else if (description.trim().length < MIN_DESCRIPTION_LENGTH) {
      found.description = `Agrega un poco más de detalle (mínimo ${MIN_DESCRIPTION_LENGTH} caracteres).`
    }
    if (attachment && attachment.size > MAX_ATTACHMENT_BYTES) {
      found.attachment = 'El archivo pesa más de 5 MB. Elige uno más ligero.'
    }
    return found
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const found = validate()
    setErrors(found)
    if (Object.keys(found).length > 0) {
      setSubmitAttempts((count) => count + 1)
      return
    }
    onSubmit({
      requester: requester.trim(),
      department,
      description: description.trim(),
      details,
      attachmentName: attachment?.name,
    })
  }

  return (
    <Card>
      <form ref={formRef} noValidate onSubmit={handleSubmit} aria-labelledby="formulario-titulo">
        <CardHeader className="gap-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="-ml-3 w-fit text-slate-500"
            onClick={onCancel}
          >
            <ArrowLeft size={16} aria-hidden="true" />
            Volver al catálogo
          </Button>
          <h3 id="formulario-titulo" className="text-xl font-bold text-slate-900">
            Nueva petición de servicio
          </h3>
          <CardDescription>
            Los campos con <span className="text-red-600">*</span> son obligatorios.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-8 pt-6">
          {/* Tipo de solicitud */}
          <section aria-labelledby="tipo-titulo" className="space-y-3">
            <h4 id="tipo-titulo" className="text-base font-semibold text-slate-800">
              Tipo de solicitud
            </h4>
            <div className="flex flex-col gap-4 rounded-xl border border-purple-200 bg-purple-50 p-4 sm:flex-row sm:items-center">
              <span className="w-fit rounded-lg bg-white p-2.5 text-purple-700 shadow-sm">
                <CategoryIcon size={20} aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1 space-y-1">
                <p className="text-xs font-medium text-purple-700">{category.label}</p>
                <p className="text-base font-semibold text-slate-800">{service.name}</p>
                <p className="text-sm text-slate-600">{service.description}</p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <Badge variant="default">
                    <Clock size={12} aria-hidden="true" />
                    Entrega: {service.estimatedDelivery}
                  </Badge>
                  {service.requiresApproval ? (
                    <Badge variant="warning">
                      <ShieldCheck size={12} aria-hidden="true" />
                      Requiere aprobación
                    </Badge>
                  ) : (
                    <Badge variant="success">
                      <Zap size={12} aria-hidden="true" />
                      Sin aprobación
                    </Badge>
                  )}
                </div>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={onCancel}>
                Cambiar servicio
              </Button>
            </div>
          </section>

          {/* Datos del solicitante */}
          <section aria-labelledby="datos-titulo" className="space-y-3">
            <h4 id="datos-titulo" className="text-base font-semibold text-slate-800">
              Tus datos
            </h4>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Field label="Nombre completo" htmlFor="requester" required error={errors.requester}>
                <Input
                  id="requester"
                  autoComplete="name"
                  placeholder="Ej. Ana López"
                  value={requester}
                  invalid={Boolean(errors.requester)}
                  aria-describedby={describedBy('requester', Boolean(errors.requester))}
                  onChange={(event) => {
                    setRequester(event.target.value)
                    clearError('requester')
                  }}
                />
              </Field>
              <Field label="Departamento" htmlFor="department" required error={errors.department}>
                <Select
                  id="department"
                  value={department}
                  invalid={Boolean(errors.department)}
                  aria-describedby={describedBy('department', Boolean(errors.department))}
                  onChange={(event) => {
                    setDepartment(event.target.value)
                    clearError('department')
                  }}
                >
                  <option value="" disabled>
                    Elige una opción
                  </option>
                  {DEPARTMENTS.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field
                label="Fecha de registro"
                htmlFor="created-at"
                hint="Se asigna automáticamente."
              >
                <Input
                  id="created-at"
                  value={today}
                  disabled
                  aria-describedby={describedBy('created-at', true)}
                />
              </Field>
            </div>
          </section>

          {/* Detalles de la petición */}
          <section aria-labelledby="detalles-titulo" className="space-y-3">
            <h4 id="detalles-titulo" className="text-base font-semibold text-slate-800">
              Detalles de la petición
            </h4>
            {service.extraFields.length > 0 && (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {service.extraFields.map((field) => {
                  const id = `extra-${field.id}`
                  const error = errors[id]
                  const value = details[field.id] ?? ''
                  const update = (next: string) => {
                    setDetails((current) => ({ ...current, [field.id]: next }))
                    clearError(id)
                  }
                  return (
                    <Field
                      key={field.id}
                      label={field.label}
                      htmlFor={id}
                      required={field.required}
                      error={error}
                    >
                      {field.type === 'select' ? (
                        <Select
                          id={id}
                          value={value}
                          invalid={Boolean(error)}
                          aria-describedby={describedBy(id, Boolean(error))}
                          onChange={(event) => update(event.target.value)}
                        >
                          <option value="" disabled>
                            Elige una opción
                          </option>
                          {field.options?.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      ) : (
                        <Input
                          id={id}
                          value={value}
                          placeholder={field.placeholder}
                          invalid={Boolean(error)}
                          aria-describedby={describedBy(id, Boolean(error))}
                          onChange={(event) => update(event.target.value)}
                        />
                      )}
                    </Field>
                  )
                })}
              </div>
            )}

            <Field
              label="Descripción o justificación"
              htmlFor="description"
              required
              error={errors.description}
              hint="Cuéntanos para qué lo necesitas; así la aprueban y la atienden más rápido."
            >
              <Textarea
                id="description"
                value={description}
                placeholder="Ej. Lo necesito para consultar los reportes de cierre mensual."
                invalid={Boolean(errors.description)}
                aria-describedby={describedBy('description', true)}
                onChange={(event) => {
                  setDescription(event.target.value)
                  clearError('description')
                }}
              />
            </Field>

            <div className="space-y-1.5">
              <p className="text-sm font-medium text-slate-700">Archivo adjunto (opcional)</p>
              <div className="flex items-center gap-2">
                <label
                  htmlFor="attachment"
                  className="relative flex flex-1 cursor-pointer items-center gap-3 rounded-lg border border-dashed border-border bg-white px-4 py-3 text-sm text-slate-600 transition-colors hover:bg-surface-muted focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-1"
                >
                  <Paperclip size={16} aria-hidden="true" className="shrink-0 text-slate-400" />
                  <span className="truncate">
                    {attachment
                      ? attachment.name
                      : 'Elige un archivo: PDF, imagen o Word (máx. 5 MB)'}
                  </span>
                  <input
                    ref={fileInputRef}
                    id="attachment"
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
                    className="sr-only"
                    aria-invalid={Boolean(errors.attachment) || undefined}
                    aria-describedby={describedBy('attachment', Boolean(errors.attachment))}
                    onChange={(event) => {
                      setAttachment(event.target.files?.[0] ?? null)
                      clearError('attachment')
                    }}
                  />
                </label>
                {attachment && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label="Quitar archivo adjunto"
                    onClick={() => {
                      setAttachment(null)
                      clearError('attachment')
                      if (fileInputRef.current) fileInputRef.current.value = ''
                    }}
                  >
                    <X size={16} aria-hidden="true" />
                  </Button>
                )}
              </div>
              {errors.attachment && (
                <p id="attachment-description" className="text-xs font-medium text-red-700">
                  {errors.attachment}
                </p>
              )}
            </div>
          </section>

          {service.requiresApproval && (
            <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-700">
              <ShieldCheck size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
              <p>
                Este servicio necesita la <strong>aprobación de un responsable</strong>. Te
                avisaremos en cuanto la autoricen.
              </p>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex-col-reverse gap-3 border-t border-border/50 pt-6 sm:flex-row sm:justify-end">
          <Button type="button" variant="outline" className="w-full sm:w-auto" onClick={onCancel}>
            Cancelar
          </Button>
          <Button type="submit" className="w-full sm:w-auto">
            <Send size={16} aria-hidden="true" />
            Enviar petición
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}
