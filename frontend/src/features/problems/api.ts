// Integración del módulo de Problemas con services/problems.
// Llama a la API real y, si el servicio no responde, usa los datos de ejemplo.
import { ApiError } from '@/api/client'
import { listarErroresConocidos, listarProblemas } from '@/api/problems'
import { cargarDatosDeEjemplo } from './data'
import type { DatosProblemas } from './types'

function servicioInalcanzable(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 404 || error.status >= 500
  return true
}

/**
 * Carga los datos desde la API. El contrato v0 no expone los vínculos de incidentes ni el
 * análisis de 5 porqués, así que esos quedan vacíos cuando la API responde; con el servicio
 * caído se devuelven los datos de ejemplo completos.
 */
export async function cargarProblemasConRespaldo(): Promise<DatosProblemas> {
  try {
    const [problemas, errores] = await Promise.all([listarProblemas(), listarErroresConocidos()])
    return { problemas: problemas.results, incidentes: [], errores: errores.results, analisis: {} }
  } catch (error) {
    if (!servicioInalcanzable(error)) throw error
    return cargarDatosDeEjemplo()
  }
}
