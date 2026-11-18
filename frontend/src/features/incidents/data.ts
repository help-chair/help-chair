import type { BadgeProps } from '@/components/ui/badge'
import type {
  Channel,
  Escalation,
  EscalationLevel,
  Impact,
  Priority,
  Ticket,
  TicketStatus,
  Urgency,
} from './types'

// Catálogos, datos de ejemplo (mocks) y cálculos del módulo mientras services/incidents
// publica su API. Los casos son los del diseño en Figma (frontend/docs/incidents/).

export type BadgeVariant = NonNullable<BadgeProps['variant']>

export interface Option<T extends string> {
  value: T
  label: string
  variant: BadgeVariant
}

export const CHANNEL_LABEL: Record<Channel, string> = { email: 'Email', telefono: 'Teléfono' }

export const URGENCY_OPTIONS: Option<Urgency>[] = [
  { value: 'alta', label: 'Alta', variant: 'exception' },
  { value: 'media', label: 'Media', variant: 'warning' },
  { value: 'baja', label: 'Baja', variant: 'success' },
]

export const PRIORITY_OPTIONS: Option<Priority>[] = [
  { value: 'urgente', label: 'Urgente', variant: 'exception' },
  { value: 'alta', label: 'Alta', variant: 'warning' },
  { value: 'media', label: 'Media', variant: 'info' },
  { value: 'baja', label: 'Baja', variant: 'request' },
]

export const IMPACT_OPTIONS: Option<Impact>[] = [
  { value: 'alto', label: 'Alto', variant: 'exception' },
  { value: 'medio', label: 'Medio', variant: 'warning' },
  { value: 'bajo', label: 'Bajo', variant: 'success' },
]

export function findOption<T extends string>(options: Option<T>[], value: T): Option<T> {
  return options.find((option) => option.value === value) ?? options[0]
}

/** Punto de color de cada tono, con los mismos tokens ITIL que usa el `Badge`. */
export const TONE_DOT: Record<BadgeVariant, string> = {
  default: 'bg-slate-400',
  outline: 'bg-slate-400',
  info: 'bg-itil-info',
  warning: 'bg-itil-warning',
  exception: 'bg-itil-exception',
  success: 'bg-itil-success',
  request: 'bg-itil-request',
}

/** Color de las barras del indicador de nivel. */
export const LEVEL_TONE: Record<EscalationLevel, string> = {
  1: TONE_DOT.info,
  2: TONE_DOT.warning,
  3: TONE_DOT.exception,
}

export const STATUS_LABEL: Record<TicketStatus, string> = {
  abierto: 'Ticket abierto',
  cerrado: 'Ticket cerrado',
}

/** A quién debe llamar Incidentes según el nivel al que se escaló el caso. */
export const CALL_TARGET: Record<Escalation['level'], string> = {
  2: 'a un supervisor',
  3: 'al jefe de área',
}

// Evidencia: los formatos y el límite que muestra el diseño.
export const EVIDENCE_ACCEPT = '.png,.jpg,.jpeg,.pdf,.txt'
export const EVIDENCE_MAX_BYTES = 10 * 1024 * 1024

/** Devuelve por qué se rechaza el archivo, o `null` si es válido. */
export function evidenceError(file: File): string | null {
  const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!EVIDENCE_ACCEPT.split(',').includes(extension)) {
    return 'Formato no permitido. Usa PNG, JPG, PDF o TXT.'
  }
  if (file.size > EVIDENCE_MAX_BYTES) {
    return 'El archivo pesa más de 10 MB. Elige uno más ligero.'
  }
  return null
}

const MINUTE = 60_000
const HOUR = 60 * MINUTE

function minutesAgo(now: number, minutes: number) {
  return new Date(now - minutes * MINUTE).toISOString()
}

/**
 * Casos del diseño en Figma. Las horas son relativas al momento de carga para que
 * los indicadores («nuevo en la última hora», «hace 12 min») tengan sentido.
 */
export function createSampleData(now = Date.now()): {
  tickets: Ticket[]
  escalations: Escalation[]
} {
  const tickets: Ticket[] = [
    {
      id: 'TCK-1049',
      createdAt: minutesAgo(now, 55),
      requesterId: 'A-1021',
      requesterName: 'Ana Ruiz',
      channel: 'email',
      description: 'Sin acceso al sistema escolar',
      urgency: 'alta',
      priority: 'urgente',
      impact: 'alto',
      status: 'abierto',
      level: 1,
      evidenceName: 'captura-error-acceso.png',
    },
    {
      id: 'TCK-1048',
      createdAt: minutesAgo(now, 60),
      requesterId: 'A-1034',
      requesterName: 'Luis Mora',
      channel: 'telefono',
      description: 'Impresora del laboratorio no responde',
      urgency: 'media',
      priority: 'media',
      impact: 'medio',
      status: 'abierto',
      level: 2,
    },
    {
      id: 'TCK-1047',
      createdAt: minutesAgo(now, 68),
      requesterId: 'A-1040',
      requesterName: 'Sofía Vega',
      channel: 'email',
      description: 'Solicitud de licencia de software',
      urgency: 'baja',
      priority: 'baja',
      impact: 'bajo',
      status: 'cerrado',
      level: 1,
      closedAt: minutesAgo(now, 30),
    },
    {
      id: 'TCK-1046',
      createdAt: minutesAgo(now, 75),
      requesterId: 'A-1007',
      requesterName: 'Jorge Páez',
      channel: 'telefono',
      description: 'Servidor de base de datos caído',
      urgency: 'alta',
      priority: 'urgente',
      impact: 'alto',
      status: 'abierto',
      level: 3,
      evidenceName: 'log-servidor-bd.txt',
    },
    {
      id: 'TCK-1045',
      createdAt: minutesAgo(now, 82),
      requesterId: 'A-1052',
      requesterName: 'María Cruz',
      channel: 'email',
      description: 'Wi-Fi caído en el edificio B',
      urgency: 'alta',
      priority: 'alta',
      impact: 'medio',
      status: 'abierto',
      level: 2,
      evidenceName: 'reporte-wifi-edificio-b.pdf',
    },
    {
      id: 'TCK-1044',
      createdAt: minutesAgo(now, 100),
      requesterId: 'A-1013',
      requesterName: 'Carlos Ibarra',
      channel: 'telefono',
      description: 'Correo institucional no envía mensajes',
      urgency: 'media',
      priority: 'media',
      impact: 'medio',
      status: 'cerrado',
      level: 1,
      closedAt: minutesAgo(now, 50),
    },
  ]

  const escalations: Escalation[] = [
    { id: 'ESC-TCK-1046-3', ticketId: 'TCK-1046', level: 3, escalatedAt: minutesAgo(now, 12) },
    { id: 'ESC-TCK-1045-2', ticketId: 'TCK-1045', level: 2, escalatedAt: minutesAgo(now, 25) },
    { id: 'ESC-TCK-1048-2', ticketId: 'TCK-1048', level: 2, escalatedAt: minutesAgo(now, 40) },
  ]

  return { tickets, escalations }
}

export function nextTicketId(tickets: Ticket[]) {
  const highest = tickets.reduce((max, ticket) => {
    const number = Number(ticket.id.replace('TCK-', ''))
    return Number.isNaN(number) ? max : Math.max(max, number)
  }, 1000)
  return `TCK-${highest + 1}`
}

/** Indicadores de la fila superior; se calculan solos a partir de los tickets. */
export function computeMetrics(tickets: Ticket[], now: number) {
  const open = tickets.filter((ticket) => ticket.status === 'abierto')
  const today = new Date(now).toDateString()
  return {
    open: open.length,
    newLastHour: open.filter((ticket) => now - Date.parse(ticket.createdAt) < HOUR).length,
    closedToday: tickets.filter(
      (ticket) => ticket.closedAt && new Date(ticket.closedAt).toDateString() === today,
    ).length,
    urgentActive: open.filter((ticket) => ticket.priority === 'urgente').length,
    escalated: open.filter((ticket) => ticket.level > 1).length,
    atMaxLevel: open.filter((ticket) => ticket.level === 3).length,
  }
}

export type Metrics = ReturnType<typeof computeMetrics>

const timeFormatter = new Intl.DateTimeFormat('es-MX', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})

export function formatTime(iso: string) {
  return timeFormatter.format(new Date(iso))
}

export function formatElapsed(iso: string, now: number) {
  const minutes = Math.max(0, Math.floor((now - Date.parse(iso)) / MINUTE))
  if (minutes < 1) return 'hace un momento'
  if (minutes < 60) return `hace ${minutes} min`
  return `hace ${Math.floor(minutes / 60)} h`
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
