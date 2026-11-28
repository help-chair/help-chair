import {
  AppWindow,
  Archive,
  Ban,
  CheckCircle2,
  Hourglass,
  KeyRound,
  Laptop,
  Package,
  Phone,
  RotateCcw,
  Send,
  UserCheck,
  type LucideIcon,
} from 'lucide-react'
import type { BadgeProps } from '@/components/ui/badge'
import type {
  ApprovalStatus,
  CatalogService,
  RequestStatus,
  ServiceCategory,
  ServiceRequest,
} from './types'

type BadgeVariant = NonNullable<BadgeProps['variant']>

// Datos de ejemplo (mocks) mientras services/requests publica su API.

export const CATEGORIES: { id: ServiceCategory; label: string; icon: LucideIcon }[] = [
  { id: 'hardware', label: 'Hardware', icon: Laptop },
  { id: 'software', label: 'Software', icon: AppWindow },
  { id: 'accesos', label: 'Permisos y accesos', icon: KeyRound },
  { id: 'telefonia', label: 'Telefonía', icon: Phone },
]

export function getCategory(id: ServiceCategory) {
  return CATEGORIES.find((category) => category.id === id) ?? CATEGORIES[0]
}

export const DEPARTMENTS = [
  'Dirección',
  'Finanzas',
  'Operaciones',
  'Recursos Humanos',
  'Sistemas',
  'Ventas',
]

const ACCESS_LEVELS = ['Solo lectura', 'Lectura y escritura', 'Administrador']

export const CATALOG: CatalogService[] = [
  {
    id: 'hw-equipo',
    name: 'Equipo de cómputo nuevo',
    description: 'Laptop o computadora de escritorio para un colaborador.',
    category: 'hardware',
    estimatedDelivery: '5 días hábiles',
    requiresApproval: true,
    extraFields: [
      {
        id: 'tipo-equipo',
        label: 'Tipo de equipo',
        type: 'select',
        options: ['Laptop', 'Computadora de escritorio'],
        required: true,
      },
      {
        id: 'uso',
        label: 'Uso principal',
        type: 'select',
        options: ['Oficina', 'Desarrollo', 'Diseño'],
        required: true,
      },
    ],
  },
  {
    id: 'hw-perifericos',
    name: 'Periféricos',
    description: 'Mouse, teclado, monitor, audífonos o cámara web.',
    category: 'hardware',
    estimatedDelivery: '2 días hábiles',
    requiresApproval: false,
    extraFields: [
      {
        id: 'periferico',
        label: 'Periférico',
        type: 'select',
        options: ['Mouse', 'Teclado', 'Monitor', 'Audífonos', 'Cámara web'],
        required: true,
      },
    ],
  },
  {
    id: 'sw-instalacion',
    name: 'Instalación de programa',
    description: 'Instalamos en tu equipo un programa autorizado por la empresa.',
    category: 'software',
    estimatedDelivery: '1 día hábil',
    requiresApproval: false,
    extraFields: [
      {
        id: 'programa',
        label: 'Programa',
        type: 'text',
        placeholder: 'Ej. Visual Studio Code',
        required: true,
      },
      {
        id: 'inventario',
        label: 'Número de inventario del equipo',
        type: 'text',
        placeholder: 'Ej. PC-0231',
      },
    ],
  },
  {
    id: 'sw-licencia',
    name: 'Licencia de software',
    description: 'Licencia de un programa de pago, como Office o Adobe.',
    category: 'software',
    estimatedDelivery: '3 días hábiles',
    requiresApproval: true,
    extraFields: [
      {
        id: 'software',
        label: 'Software',
        type: 'text',
        placeholder: 'Ej. Adobe Acrobat Pro',
        required: true,
      },
    ],
  },
  {
    id: 'acc-servidor',
    name: 'Acceso a servidor',
    description: 'Permiso para entrar a un servidor de la empresa.',
    category: 'accesos',
    estimatedDelivery: '1 día hábil',
    requiresApproval: true,
    extraFields: [
      {
        id: 'servidor',
        label: 'Servidor',
        type: 'text',
        placeholder: 'Ej. srv-app-01',
        required: true,
      },
      {
        id: 'nivel',
        label: 'Nivel de acceso',
        type: 'select',
        options: ACCESS_LEVELS,
        required: true,
      },
    ],
  },
  {
    id: 'acc-carpeta',
    name: 'Acceso a carpeta compartida',
    description: 'Permiso para ver o editar una carpeta de la red.',
    category: 'accesos',
    estimatedDelivery: '4 horas',
    requiresApproval: false,
    extraFields: [
      {
        id: 'ruta',
        label: 'Ruta de la carpeta',
        type: 'text',
        placeholder: 'Ej. \\\\archivos\\finanzas\\2026',
        required: true,
      },
      {
        id: 'permiso',
        label: 'Permiso',
        type: 'select',
        options: ACCESS_LEVELS.slice(0, 2),
        required: true,
      },
    ],
  },
  {
    id: 'acc-vpn',
    name: 'Cuenta de VPN',
    description: 'Conéctate a la red de la empresa desde fuera de la oficina.',
    category: 'accesos',
    estimatedDelivery: '1 día hábil',
    requiresApproval: true,
    extraFields: [],
  },
  {
    id: 'tel-linea',
    name: 'Línea o extensión telefónica',
    description: 'Alta de una extensión de oficina o de una línea móvil corporativa.',
    category: 'telefonia',
    estimatedDelivery: '3 días hábiles',
    requiresApproval: true,
    extraFields: [
      {
        id: 'tipo-linea',
        label: 'Tipo de línea',
        type: 'select',
        options: ['Extensión de oficina', 'Línea móvil'],
        required: true,
      },
    ],
  },
]

/** Estados de la petición en el orden del flujo, con su etiqueta y tono ITIL. */
export const REQUEST_STATES: {
  id: RequestStatus
  label: string
  description: string
  icon: LucideIcon
  badge: BadgeVariant
}[] = [
  {
    id: 'nuevo',
    label: 'Nueva',
    description: 'La petición quedó registrada.',
    icon: Send,
    badge: 'info',
  },
  {
    id: 'asignado',
    label: 'Asignada',
    description: 'Un agente de soporte ya la tiene.',
    icon: UserCheck,
    badge: 'request',
  },
  {
    id: 'en_proceso',
    label: 'En proceso',
    description: 'Soporte está preparando el servicio.',
    icon: Package,
    badge: 'request',
  },
  {
    id: 'resuelto',
    label: 'Resuelta',
    description: 'Soporte la entregó. Confirma y califica la atención.',
    icon: CheckCircle2,
    badge: 'success',
  },
  {
    id: 'cerrado',
    label: 'Cerrada',
    description: 'La petición terminó.',
    icon: Archive,
    badge: 'default',
  },
  {
    id: 'reabierto',
    label: 'Reabierta',
    description: 'La reabriste; soporte la retomará.',
    icon: RotateCcw,
    badge: 'warning',
  },
  {
    id: 'cancelado',
    label: 'Cancelada',
    description: 'La petición se canceló.',
    icon: Ban,
    badge: 'outline',
  },
]

export function getStatus(id: RequestStatus) {
  return REQUEST_STATES.find((state) => state.id === id) ?? REQUEST_STATES[0]
}

/** Paso de aprobación de la línea de vida (solo si el servicio la exige). */
export const APPROVAL_STEP = {
  label: 'Aprobación',
  description: 'Un responsable debe autorizarla.',
  icon: Hourglass,
}

/** Etiqueta de aprobación que se muestra junto al estado (solo cuando aporta información). */
export const APPROVAL_BADGE: Partial<
  Record<ApprovalStatus, { label: string; variant: BadgeVariant }>
> = {
  pendiente: { label: 'Por aprobar', variant: 'warning' },
  rechazado: { label: 'No aprobada', variant: 'exception' },
}

/** Estados en los que soporte sigue trabajando (y el solicitante aún puede cancelar). */
export function isActive(request: Pick<ServiceRequest, 'status' | 'approvalStatus'>) {
  return (
    ['nuevo', 'asignado', 'en_proceso', 'reabierto'].includes(request.status) &&
    request.approvalStatus !== 'rechazado'
  )
}

/** El solicitante califica al resolverse o cerrarse, si aún no lo hizo. */
export function canAnswerSurvey(request: Pick<ServiceRequest, 'status' | 'survey'>) {
  return (request.status === 'resuelto' || request.status === 'cerrado') && !request.survey
}

export const INITIAL_REQUESTS: ServiceRequest[] = [
  {
    id: 'REQ-0015',
    serviceId: 'acc-servidor',
    serviceName: 'Acceso a servidor',
    category: 'accesos',
    requester: 'Ana López',
    department: 'Finanzas',
    description: 'Necesito consultar los reportes de cierre mensual que están en el servidor.',
    details: { servidor: 'srv-reportes-02', nivel: 'Solo lectura' },
    createdAt: '2026-11-14T16:20:00Z',
    status: 'nuevo',
    approvalStatus: 'pendiente',
  },
  {
    id: 'REQ-0014',
    serviceId: 'sw-instalacion',
    serviceName: 'Instalación de programa',
    category: 'software',
    requester: 'Luis Hernández',
    department: 'Sistemas',
    description: 'Lo necesito para el desarrollo del nuevo portal interno.',
    details: { programa: 'Visual Studio Code', inventario: 'PC-0231' },
    createdAt: '2026-11-13T15:05:00Z',
    status: 'en_proceso',
    approvalStatus: 'no_requerida',
  },
  {
    id: 'REQ-0013',
    serviceId: 'sw-licencia',
    serviceName: 'Licencia de software',
    category: 'software',
    requester: 'Carla Méndez',
    department: 'Ventas',
    description: 'Para firmar y editar contratos en PDF con clientes.',
    details: { software: 'Adobe Acrobat Pro' },
    createdAt: '2026-11-12T18:40:00Z',
    status: 'asignado',
    approvalStatus: 'aprobado',
  },
  {
    id: 'REQ-0012',
    serviceId: 'hw-perifericos',
    serviceName: 'Periféricos',
    category: 'hardware',
    requester: 'María Torres',
    department: 'Recursos Humanos',
    description: 'Mi monitor actual parpadea y no puedo trabajar bien.',
    details: { periferico: 'Monitor' },
    createdAt: '2026-11-10T14:00:00Z',
    status: 'resuelto',
    approvalStatus: 'no_requerida',
  },
  {
    id: 'REQ-0011',
    serviceId: 'acc-vpn',
    serviceName: 'Cuenta de VPN',
    category: 'accesos',
    requester: 'Jorge Salinas',
    department: 'Operaciones',
    description: 'Voy a trabajar desde casa dos días por semana.',
    details: {},
    createdAt: '2026-11-06T17:30:00Z',
    status: 'cerrado',
    approvalStatus: 'aprobado',
    survey: {
      rating: 5,
      comment: 'Me la configuraron el mismo día.',
      answeredAt: '2026-11-07T19:10:00Z',
    },
  },
  {
    id: 'REQ-0010',
    serviceId: 'acc-carpeta',
    serviceName: 'Acceso a carpeta compartida',
    category: 'accesos',
    requester: 'Paola Ríos',
    department: 'Dirección',
    description: 'Necesito ver los presupuestos del área.',
    details: { ruta: '\\\\archivos\\direccion\\2026', permiso: 'Solo lectura' },
    createdAt: '2026-11-05T15:45:00Z',
    status: 'cancelado',
    approvalStatus: 'no_requerida',
    cancelReason: 'La registré por error: era otra carpeta.',
  },
]

export function nextRequestId(requests: ServiceRequest[]) {
  const highest = requests.reduce((max, request) => {
    const number = Number(request.id.replace('REQ-', ''))
    return Number.isNaN(number) ? max : Math.max(max, number)
  }, 0)
  return `REQ-${String(highest + 1).padStart(4, '0')}`
}

const dateFormatter = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

export function formatDate(date: string | Date) {
  return dateFormatter.format(typeof date === 'string' ? new Date(date) : date)
}
