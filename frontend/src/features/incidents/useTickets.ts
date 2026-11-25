import { useCallback, useEffect, useReducer, useState } from 'react'
import { mensajeDeError } from '@/api/client'
import { cargarIncidentes, cerrarIncidente, escalarIncidente, registrarIncidente } from './api'
import type { Escalation, EscalationLevel, NewTicketInput, Ticket } from './types'

// Estado del módulo: todo sale de services/incidents. Crear, escalar y cerrar esperan la respuesta
// del servicio; solo «marcar llamada» vive en memoria porque el contrato no tiene ese dato.

export type EstadoCarga = 'cargando' | 'lista' | 'error'

/** La acción salió bien o devuelve el mensaje de error para mostrarlo. */
export type Resultado<T> = { ok: true; valor: T } | { ok: false; detalle: string }

interface TicketsState {
  tickets: Ticket[]
  escalations: Escalation[]
}

type Action =
  | { type: 'load'; tickets: Ticket[]; escalations: Escalation[] }
  | { type: 'replace'; ticket: Ticket; escalation?: Escalation }
  | { type: 'close'; ticket: Ticket }
  | { type: 'create'; ticket: Ticket }
  | { type: 'markCalled'; escalationId: string; at: string }

function ticketsReducer(state: TicketsState, action: Action): TicketsState {
  switch (action.type) {
    case 'load':
      return { tickets: action.tickets, escalations: action.escalations }
    case 'replace':
      return {
        tickets: state.tickets.map((item) => (item.id === action.ticket.id ? action.ticket : item)),
        escalations: action.escalation
          ? [action.escalation, ...state.escalations]
          : state.escalations,
      }
    case 'close':
      return {
        tickets: state.tickets.map((item) => (item.id === action.ticket.id ? action.ticket : item)),
        // Al cerrar el caso se retiran sus avisos de llamada que seguían pendientes.
        escalations: state.escalations.filter(
          (escalation) => escalation.ticketId !== action.ticket.id || escalation.calledAt,
        ),
      }
    case 'create':
      return { ...state, tickets: [action.ticket, ...state.tickets] }
    case 'markCalled':
      return {
        ...state,
        escalations: state.escalations.map((escalation): Escalation =>
          escalation.id === action.escalationId && !escalation.calledAt
            ? { ...escalation, calledAt: action.at }
            : escalation,
        ),
      }
  }
}

/** Incidentes y avisos de escalamiento con sus acciones: escalar, cerrar, crear y marcar llamada. */
export function useTickets(cargar = cargarIncidentes) {
  const [state, dispatch] = useReducer(ticketsReducer, undefined, () => ({
    tickets: [],
    escalations: [],
  }))
  const [carga, setCarga] = useState<EstadoCarga>('cargando')
  const [errorCarga, setErrorCarga] = useState('')

  const recargar = useCallback(() => {
    setCarga('cargando')
    cargar().then(
      (datos) => {
        dispatch({ type: 'load', ...datos })
        setCarga('lista')
      },
      (error: unknown) => {
        setErrorCarga(mensajeDeError(error, 'Verifica tu conexión con el servicio de Incidencias.'))
        setCarga('error')
      },
    )
  }, [cargar])

  /** Vuelve a leer la lista sin mostrar la carga (tras un fallo a medias, p. ej.). */
  const sincronizar = useCallback(() => {
    cargar().then(
      (datos) => dispatch({ type: 'load', ...datos }),
      () => undefined,
    )
  }, [cargar])

  useEffect(() => {
    recargar()
  }, [recargar])

  /** Sube el caso un nivel en el servicio y devuelve el nivel nuevo. */
  async function escalate(ticketId: string): Promise<Resultado<EscalationLevel>> {
    const ticket = state.tickets.find((item) => item.id === ticketId)
    if (!ticket || ticket.status !== 'abierto' || ticket.level === 3) {
      return { ok: false, detalle: `${ticketId} ya no se puede escalar.` }
    }
    try {
      const actualizado = await escalarIncidente(ticket)
      const escalation: Escalation = {
        id: `ESC-${actualizado.id}-${actualizado.level}`,
        ticketId: actualizado.id,
        level: actualizado.level as Escalation['level'],
        escalatedAt: new Date().toISOString(),
      }
      dispatch({ type: 'replace', ticket: actualizado, escalation })
      return { ok: true, valor: actualizado.level }
    } catch (error) {
      return { ok: false, detalle: mensajeDeError(error, `No se pudo escalar ${ticketId}.`) }
    }
  }

  /** Cierra el caso en el servicio y devuelve cuántos avisos de llamada pendientes se retiraron. */
  async function close(ticketId: string, agenteId?: string): Promise<Resultado<number>> {
    const ticket = state.tickets.find((item) => item.id === ticketId)
    if (!ticket || ticket.status !== 'abierto') {
      return { ok: false, detalle: `${ticketId} ya está cerrado.` }
    }
    const pendientes = state.escalations.filter(
      (escalation) => escalation.ticketId === ticketId && !escalation.calledAt,
    ).length
    try {
      dispatch({ type: 'close', ticket: await cerrarIncidente(ticket, agenteId) })
      return { ok: true, valor: pendientes }
    } catch (error) {
      // El cierre son varios pasos: si uno falla, se relee el estado real del servicio.
      sincronizar()
      return { ok: false, detalle: mensajeDeError(error, `No se pudo cerrar ${ticketId}.`) }
    }
  }

  /** Registra el caso en el servicio y devuelve su código (p. ej. INC-000042). */
  async function create(input: NewTicketInput): Promise<Resultado<string>> {
    try {
      const ticket = await registrarIncidente(input)
      dispatch({ type: 'create', ticket })
      return { ok: true, valor: ticket.id }
    } catch (error) {
      return { ok: false, detalle: mensajeDeError(error, 'No se pudo registrar el incidente.') }
    }
  }

  function markCalled(escalationId: string) {
    dispatch({ type: 'markCalled', escalationId, at: new Date().toISOString() })
  }

  return { ...state, carga, errorCarga, recargar, escalate, close, create, markCalled }
}

/** Hora actual que se renueva cada minuto («hace 12 min», «nuevo en la última hora»). */
export function useNow(intervalMs = 60_000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs)
    return () => window.clearInterval(id)
  }, [intervalMs])
  return now
}
