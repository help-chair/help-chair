import { useCallback, useEffect, useState } from 'react'
import { cargarProblemasConRespaldo } from './api'
import { codigoProblema, requiereCausaRaiz, siguienteEstado } from './data'
import type {
  CambioEstado,
  DatosProblemas,
  ErrorConocido,
  ErrorConocidoCrear,
  Problema,
  ProblemaCrear,
  ProblemaIncidente,
} from './types'

// Estado del módulo en memoria (se pierde al recargar). Cada acción sigue las reglas del contrato
// (contracts/problems/openapi.yaml); para conectarlo a services/problems, cambia el cuerpo de
// estas funciones por llamadas a la API en src/api/ y los componentes no cambian.

export type EstadoCarga = 'cargando' | 'lista' | 'error'

/** Igual que la API: la acción sale bien o devuelve el `detalle` del error. */
export type Resultado<T> = { ok: true; valor: T } | { ok: false; detalle: string }

const VACIO: DatosProblemas = { problemas: [], incidentes: [], errores: [], analisis: {} }

const ahora = () => new Date().toISOString()

const siguienteId = (lista: { id: number }[]) => Math.max(0, ...lista.map((item) => item.id)) + 1

export function useProblemas(cargar: () => Promise<DatosProblemas> = cargarProblemasConRespaldo) {
  const [carga, setCarga] = useState<EstadoCarga>('cargando')
  const [datos, setDatos] = useState<DatosProblemas>(VACIO)

  const recargar = useCallback(() => {
    let vigente = true
    setCarga('cargando')
    cargar().then(
      (nuevos) => {
        if (!vigente) return
        setDatos(nuevos)
        setCarga('lista')
      },
      () => {
        if (vigente) setCarga('error')
      },
    )
    return () => {
      vigente = false
    }
  }, [cargar])

  useEffect(() => recargar(), [recargar])

  /** POST /problemas/: se crea en estado `registrado`. */
  function registrar(entrada: ProblemaCrear): Problema {
    const fecha = ahora()
    const nuevo: Problema = {
      id: siguienteId(datos.problemas),
      titulo: entrada.titulo,
      descripcion: entrada.descripcion,
      estado: 'registrado',
      prioridad: entrada.prioridad ?? 'media',
      origen: entrada.origen ?? 'manual',
      causa_raiz: entrada.causa_raiz ?? '',
      asignado_a_id: entrada.asignado_a_id ?? '',
      creado_en: fecha,
      actualizado_en: fecha,
      resuelto_en: null,
    }
    setDatos((actual) => ({ ...actual, problemas: [nuevo, ...actual.problemas] }))
    return nuevo
  }

  /** POST /problemas/{id}/estado/: solo avanza al siguiente estado del ciclo de vida. */
  function cambiarEstado(problemaId: number, cambio: CambioEstado): Resultado<Problema> {
    const problema = datos.problemas.find((item) => item.id === problemaId)
    if (!problema) return { ok: false, detalle: 'No existe el problema solicitado.' }
    if (siguienteEstado(problema.estado) !== cambio.estado) {
      return {
        ok: false,
        detalle: `No se puede pasar de ${problema.estado} a ${cambio.estado}.`,
      }
    }
    const causaRaiz = cambio.causa_raiz?.trim() || problema.causa_raiz
    if (requiereCausaRaiz(cambio.estado) && !causaRaiz) {
      return { ok: false, detalle: 'Escribe la causa raíz para continuar.' }
    }
    const fecha = ahora()
    const actualizado: Problema = {
      ...problema,
      estado: cambio.estado,
      causa_raiz: causaRaiz,
      actualizado_en: fecha,
      resuelto_en: cambio.estado === 'resuelto' ? fecha : problema.resuelto_en,
    }
    setDatos((actual) => ({
      ...actual,
      problemas: actual.problemas.map((item) => (item.id === problemaId ? actualizado : item)),
    }))
    return { ok: true, valor: actualizado }
  }

  /** POST /problemas/{id}/incidentes/: responde con error si ya estaba vinculada (409). */
  function vincular(problemaId: number, incidenteId: string): Resultado<ProblemaIncidente> {
    const id = incidenteId.trim().toUpperCase()
    if (!id) return { ok: false, detalle: 'Escribe el ID de la incidencia.' }
    const repetido = datos.incidentes.some(
      (vinculo) => vinculo.problema_id === problemaId && vinculo.incidente_id === id,
    )
    if (repetido) {
      return { ok: false, detalle: `${id} ya está vinculada a ${codigoProblema(problemaId)}.` }
    }
    const vinculo: ProblemaIncidente = {
      id: siguienteId(datos.incidentes),
      problema_id: problemaId,
      incidente_id: id,
      vinculado_en: ahora(),
    }
    setDatos((actual) => ({ ...actual, incidentes: [vinculo, ...actual.incidentes] }))
    return { ok: true, valor: vinculo }
  }

  /** DELETE /problemas/{id}/incidentes/{incidente_id}/ */
  function desvincular(problemaId: number, incidenteId: string) {
    setDatos((actual) => ({
      ...actual,
      incidentes: actual.incidentes.filter(
        (vinculo) => !(vinculo.problema_id === problemaId && vinculo.incidente_id === incidenteId),
      ),
    }))
  }

  /** POST /errores-conocidos/ */
  function crearErrorConocido(entrada: ErrorConocidoCrear): ErrorConocido {
    const fecha = ahora()
    const nuevo: ErrorConocido = {
      ...entrada,
      id: siguienteId(datos.errores),
      articulo_kb_id: entrada.articulo_kb_id ?? '',
      activo: entrada.activo ?? true,
      creado_en: fecha,
      actualizado_en: fecha,
    }
    setDatos((actual) => ({ ...actual, errores: [nuevo, ...actual.errores] }))
    return nuevo
  }

  return {
    carga,
    recargar,
    ...datos,
    registrar,
    cambiarEstado,
    vincular,
    desvincular,
    crearErrorConocido,
  }
}
