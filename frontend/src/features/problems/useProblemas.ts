import { useCallback, useEffect, useState } from 'react'
import { mensajeDeError } from '@/api/client'
import {
  cambiarEstadoProblema,
  crearErrorConocido as crearErrorConocidoApi,
  crearProblema,
  desvincularIncidenteProblema,
  vincularIncidenteProblema,
} from '@/api/problems'
import { cargarProblemas } from './api'
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

// Estado del módulo: todo sale de services/problems (contracts/problems/openapi.yaml). Cada acción
// valida lo básico en la pantalla, espera la respuesta del servicio y guarda lo que este devuelve.

export type EstadoCarga = 'cargando' | 'lista' | 'error'

/** Igual que la API: la acción sale bien o devuelve el `detalle` del error. */
export type Resultado<T> = { ok: true; valor: T } | { ok: false; detalle: string }

const VACIO: DatosProblemas = { problemas: [], incidentes: [], errores: [], analisis: {} }

function fallo(error: unknown, respaldo: string): { ok: false; detalle: string } {
  return { ok: false, detalle: mensajeDeError(error, respaldo) }
}

export function useProblemas(cargar: () => Promise<DatosProblemas> = cargarProblemas) {
  const [carga, setCarga] = useState<EstadoCarga>('cargando')
  const [errorCarga, setErrorCarga] = useState('')
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
      (error: unknown) => {
        if (!vigente) return
        setErrorCarga(mensajeDeError(error, 'Verifica tu conexión con el servicio de Problemas.'))
        setCarga('error')
      },
    )
    return () => {
      vigente = false
    }
  }, [cargar])

  useEffect(() => recargar(), [recargar])

  /** POST /problemas/: el servicio lo crea en estado `registrado`. */
  async function registrar(entrada: ProblemaCrear): Promise<Resultado<Problema>> {
    try {
      const nuevo = await crearProblema(entrada)
      setDatos((actual) => ({ ...actual, problemas: [nuevo, ...actual.problemas] }))
      return { ok: true, valor: nuevo }
    } catch (error) {
      return fallo(error, 'No se pudo registrar el problema.')
    }
  }

  /** POST /problemas/{id}/estado/: solo avanza al siguiente estado del ciclo de vida. */
  async function cambiarEstado(
    problemaId: number,
    cambio: CambioEstado,
  ): Promise<Resultado<Problema>> {
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
    try {
      const actualizado = await cambiarEstadoProblema(problemaId, cambio)
      setDatos((actual) => ({
        ...actual,
        problemas: actual.problemas.map((item) => (item.id === problemaId ? actualizado : item)),
      }))
      return { ok: true, valor: actualizado }
    } catch (error) {
      return fallo(error, `No se pudo actualizar ${codigoProblema(problemaId)}.`)
    }
  }

  /** POST /problemas/{id}/incidentes/: el servicio responde 409 si ya estaba vinculada. */
  async function vincular(
    problemaId: number,
    incidenteId: string,
  ): Promise<Resultado<ProblemaIncidente>> {
    const id = incidenteId.trim().toUpperCase()
    if (!id) return { ok: false, detalle: 'Escribe el ID de la incidencia.' }
    const repetido = datos.incidentes.some(
      (vinculo) => vinculo.problema_id === problemaId && vinculo.incidente_id === id,
    )
    if (repetido) {
      return { ok: false, detalle: `${id} ya está vinculada a ${codigoProblema(problemaId)}.` }
    }
    try {
      const vinculo = await vincularIncidenteProblema(problemaId, id)
      setDatos((actual) => ({ ...actual, incidentes: [vinculo, ...actual.incidentes] }))
      return { ok: true, valor: vinculo }
    } catch (error) {
      return fallo(error, `No se pudo vincular ${id}.`)
    }
  }

  /** DELETE /problemas/{id}/incidentes/{incidente_id}/ */
  async function desvincular(problemaId: number, incidenteId: string): Promise<Resultado<null>> {
    try {
      await desvincularIncidenteProblema(problemaId, incidenteId)
      setDatos((actual) => ({
        ...actual,
        incidentes: actual.incidentes.filter(
          (vinculo) =>
            !(vinculo.problema_id === problemaId && vinculo.incidente_id === incidenteId),
        ),
      }))
      return { ok: true, valor: null }
    } catch (error) {
      return fallo(error, `No se pudo desvincular ${incidenteId}.`)
    }
  }

  /** POST /errores-conocidos/ */
  async function crearErrorConocido(
    entrada: ErrorConocidoCrear,
  ): Promise<Resultado<ErrorConocido>> {
    try {
      const nuevo = await crearErrorConocidoApi(entrada)
      setDatos((actual) => ({ ...actual, errores: [nuevo, ...actual.errores] }))
      return { ok: true, valor: nuevo }
    } catch (error) {
      return fallo(error, 'No se pudo publicar el error conocido.')
    }
  }

  return {
    carga,
    errorCarga,
    recargar,
    ...datos,
    registrar,
    cambiarEstado,
    vincular,
    desvincular,
    crearErrorConocido,
  }
}
