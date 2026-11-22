// Tipos del módulo de Base de Conocimiento (ITIL v4 · Knowledge Management).
// ⚠️ Provisionales: contracts/knowledge/openapi.yaml todavía no existe (issue #112). Usan
// snake_case, como el contrato de Problemas, para que el cambio sea mínimo cuando se publique.

export type Categoria = 'red' | 'accesos' | 'correo' | 'impresoras' | 'software' | 'base_datos'

/** publico = lo ve cualquier usuario; agentes = solo el Service Desk. */
export type Visibilidad = 'publico' | 'agentes'

export interface Articulo {
  /** Mismo formato que `articulo_kb_id` en el contrato de Problemas, p. ej. «KB-028». */
  id: string
  titulo: string
  resumen: string
  categoria: Categoria
  visibilidad: Visibilidad
  /** ID del error conocido en services/problems cuando el artículo es su solución temporal. */
  error_conocido_id: number | null
  /** Señales para saber si el artículo aplica. */
  sintomas: string[]
  pasos: string[]
  /** Qué hacer si los pasos no funcionan. */
  si_no_funciona: string
  autor: string
  /** Fecha en ISO 8601 (UTC). */
  actualizado_en: string
  consultas: number
  votos_utiles: number
  votos_no_utiles: number
}

/** Respuesta del botón «¿Te resultó útil?» (registro de uso que pide la fase 3). */
export interface Valoracion {
  articulo_id: string
  util: boolean
  comentario: string
}
