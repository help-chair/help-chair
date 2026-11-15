// Tipos del módulo de Peticiones (ITIL v4 · Service Request Management).
// Cuando exista contracts/requests/openapi.yaml, estos tipos deben generarse desde ahí.

export type ServiceCategory = 'hardware' | 'software' | 'accesos' | 'telefonia'

/** Campo adicional que pide un servicio del catálogo (ej. «Servidor» en «Acceso a servidor»). */
export interface ExtraField {
  id: string
  label: string
  type: 'text' | 'select'
  options?: string[]
  placeholder?: string
  required?: boolean
}

export interface CatalogService {
  id: string
  name: string
  description: string
  category: ServiceCategory
  /** Tiempo estimado de entrega (SLA) en texto, ej. «1 día hábil». */
  estimatedDelivery: string
  requiresApproval: boolean
  extraFields: ExtraField[]
}

/**
 * Estados de la línea de vida según frontend/DESIGN.md.
 * ⚠️ Pendiente de acordar con el backend: el issue #15 y docs/ROADMAP.md usan otras listas.
 */
export type RequestStatus = 'enviada' | 'aprobacion_pendiente' | 'en_provision' | 'completada'

export interface ServiceRequest {
  id: string
  serviceId: string
  serviceName: string
  category: ServiceCategory
  requester: string
  department: string
  description: string
  /** Respuestas a los campos adicionales del servicio, por `ExtraField.id`. */
  details: Record<string, string>
  attachmentName?: string
  /** Fecha de registro en formato ISO 8601. */
  createdAt: string
  status: RequestStatus
  requiresApproval: boolean
}

/** Lo que captura el formulario; el resto lo completa el sistema al registrar. */
export type NewRequestInput = Pick<
  ServiceRequest,
  'requester' | 'department' | 'description' | 'details' | 'attachmentName'
>
