// Integración del módulo de Problemas con services/problems (contracts/problems/openapi.yaml).
// Sin datos de ejemplo: si el servicio no responde, la pantalla muestra el error y permite reintentar.
import { listarErroresConocidos, listarIncidentesDeProblema, listarProblemas } from '@/api/problems'
import type { DatosProblemas } from './types'

/**
 * Lee problemas, errores conocidos y los incidentes vinculados a cada problema. El contrato v1
 * no expone el análisis de 5 porqués, así que queda vacío.
 */
export async function cargarProblemas(): Promise<DatosProblemas> {
  const [problemas, errores] = await Promise.all([listarProblemas(), listarErroresConocidos()])
  const vinculos = await Promise.all(
    problemas.results.map((problema) => listarIncidentesDeProblema(problema.id)),
  )
  return {
    problemas: problemas.results,
    incidentes: vinculos.flat(),
    errores: errores.results,
    analisis: {},
  }
}
