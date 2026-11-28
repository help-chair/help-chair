import { Angry, Frown, Laugh, Meh, Smile, type LucideIcon } from 'lucide-react'

// Cierre de Peticiones e Incidencias (ITIL v4): encuesta de satisfacción y motivos de cancelación.
// Se comparten entre módulos; cada módulo decide a qué endpoint enviar la respuesta.

export type Rating = 1 | 2 | 3 | 4 | 5

/** Lo que captura la encuesta. */
export interface SurveyInput {
  rating: Rating
  comment?: string
}

/** Encuesta ya respondida. */
export interface SurveyAnswer extends SurveyInput {
  /** Fecha de respuesta en formato ISO 8601. */
  answeredAt: string
}

export interface RatingOption {
  value: Rating
  label: string
  icon: LucideIcon
  /** Clases del tono ITIL cuando la opción está elegida (`peer-checked:`) o se muestra en el resumen. */
  checked: string
  tone: string
}

/** Escala de 1 a 5 con caras: el color nunca es la única señal (cada opción tiene texto). */
export const RATING_OPTIONS: RatingOption[] = [
  {
    value: 1,
    label: 'Muy mala',
    icon: Angry,
    checked: 'peer-checked:border-red-200 peer-checked:bg-red-50 peer-checked:text-red-700',
    tone: 'border-red-200 bg-red-50 text-red-700',
  },
  {
    value: 2,
    label: 'Mala',
    icon: Frown,
    checked: 'peer-checked:border-amber-200 peer-checked:bg-amber-50 peer-checked:text-amber-800',
    tone: 'border-amber-200 bg-amber-50 text-amber-800',
  },
  {
    value: 3,
    label: 'Regular',
    icon: Meh,
    checked: 'peer-checked:border-blue-200 peer-checked:bg-blue-50 peer-checked:text-blue-700',
    tone: 'border-blue-200 bg-blue-50 text-blue-700',
  },
  {
    value: 4,
    label: 'Buena',
    icon: Smile,
    checked:
      'peer-checked:border-emerald-200 peer-checked:bg-emerald-50 peer-checked:text-emerald-700',
    tone: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  {
    value: 5,
    label: 'Excelente',
    icon: Laugh,
    checked:
      'peer-checked:border-emerald-200 peer-checked:bg-emerald-50 peer-checked:text-emerald-700',
    tone: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
]

export function getRating(value: Rating) {
  return RATING_OPTIONS.find((option) => option.value === value) ?? RATING_OPTIONS[0]
}

export const COMMENT_MAX_LENGTH = 500

/** Motivos frecuentes al cancelar; «Otro motivo» obliga a escribir el detalle. */
export const CANCEL_REASONS = [
  'Ya no la necesito',
  'La resolví por mi cuenta',
  'La registré por error',
  'Está tardando demasiado',
  'Otro motivo',
] as const

export type CancelReason = (typeof CANCEL_REASONS)[number]

export const OTHER_REASON: CancelReason = 'Otro motivo'

/** El contrato de Peticiones acepta hasta 255 caracteres en `motivo_cancelacion`. */
export const CANCEL_REASON_MAX_LENGTH = 255

/** Une el motivo elegido y el detalle en el texto que se guarda en el backend. */
export function buildCancelReason(reason: CancelReason, detail: string) {
  const text = detail.trim()
  const full = reason === OTHER_REASON ? text : text ? `${reason}: ${text}` : reason
  return full.slice(0, CANCEL_REASON_MAX_LENGTH)
}
