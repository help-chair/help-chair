// Tipos del módulo de Problemas (ITIL v4 · Problem Management).
// Copiados de contracts/problems/openapi.yaml (v0.1.0): los nombres de los campos son los del contrato.

export type EstadoProblema =
  'registrado' | 'en_analisis' | 'causa_identificada' | 'error_conocido' | 'resuelto' | 'cerrado'

export type Prioridad = 'baja' | 'media' | 'alta' | 'critica'

/** manual = lo registró una persona; patron = se detectó por incidentes repetidos. */
export type Origen = 'manual' | 'patron'

export interface Problema {
  id: number
  titulo: string
  descripcion: string
  estado: EstadoProblema
  prioridad: Prioridad
  origen: Origen
  /** Cadena vacía si aún no se identifica. */
  causa_raiz: string
  /** ID del usuario en Accesos; cadena vacía si no está asignado. */
  asignado_a_id: string
  /** Fechas en ISO 8601 (UTC). */
  creado_en: string
  actualizado_en: string
  resuelto_en: string | null
}

export interface ProblemaCrear {
  titulo: string
  descripcion: string
  prioridad?: Prioridad
  origen?: Origen
  causa_raiz?: string
  asignado_a_id?: string
}

export interface CambioEstado {
  estado: EstadoProblema
  /** Se guarda en el problema junto con el cambio. */
  causa_raiz?: string
}

/** Vínculo con un incidente del servicio de Incidencias (solo su ID, sin llave foránea). */
export interface ProblemaIncidente {
  id: number
  problema_id: number
  incidente_id: string
  vinculado_en: string
}

export interface ErrorConocido {
  id: number
  problema_id: number
  titulo: string
  descripcion: string
  causa_raiz: string
  /** Solución temporal mientras no hay solución definitiva. */
  workaround: string
  /** ID del artículo en Knowledge; cadena vacía si no hay. */
  articulo_kb_id: string
  activo: boolean
  creado_en: string
  actualizado_en: string
}

export interface ErrorConocidoCrear {
  problema_id: number
  titulo: string
  descripcion: string
  causa_raiz: string
  workaround: string
  articulo_kb_id?: string
  activo?: boolean
}

// ---------------------------------------------------------------------------------------------
// Fuera del contrato v0: solo existe en el frontend y falta acordarlo con services/problems.
// ---------------------------------------------------------------------------------------------

/**
 * Un paso del análisis de los 5 porqués (DESIGN.md, página 04).
 * El contrato v0 solo guarda la conclusión en `causa_raiz`.
 */
export interface PorQue {
  pregunta: string
  respuesta: string
}

/** Todo lo que necesita la pantalla; con la API serán varias llamadas a services/problems. */
export interface DatosProblemas {
  problemas: Problema[]
  incidentes: ProblemaIncidente[]
  errores: ErrorConocido[]
  /** Análisis de 5 porqués por ID de problema. */
  analisis: Record<number, PorQue[]>
}
