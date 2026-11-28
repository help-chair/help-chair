// Tipos del módulo de Peticiones (ITIL v4 · Service Request Management).
// Los valores de `RequestStatus` y `ApprovalStatus` siguen el contrato de services/requests
// (`EstadoEnum` y `estado_aprobacion` en contracts/requests/openapi.yaml, PR #253). Cuando el
// contrato esté en develop, el resto de los campos deben generarse desde ahí.
import type { SurveyAnswer } from '@/components/closure/options'

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
 * Estado de la petición. Flujo: nuevo → asignado → en_proceso → resuelto → cerrado;
 * desde resuelto puede pasar a reabierto, y antes de resolverse, a cancelado.
 */
export type RequestStatus =
  'nuevo' | 'asignado' | 'en_proceso' | 'resuelto' | 'cerrado' | 'reabierto' | 'cancelado'

/** La aprobación va aparte del estado: una petición nueva espera aquí si su servicio la exige. */
export type ApprovalStatus = 'no_requerida' | 'pendiente' | 'aprobado' | 'rechazado'

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
  approvalStatus: ApprovalStatus
  /** `motivo_rechazo` del contrato: por qué el responsable no la aprobó. */
  rejectionReason?: string
  /** `motivo_cancelacion` del contrato: por qué el solicitante la canceló. */
  cancelReason?: string
  /** Encuesta de satisfacción respondida al cierre. */
  survey?: SurveyAnswer
}

/** Lo que captura el formulario; el resto lo completa el sistema al registrar. */
export type NewRequestInput = Pick<
  ServiceRequest,
  'requester' | 'department' | 'description' | 'details' | 'attachmentName'
>
