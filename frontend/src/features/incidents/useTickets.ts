import { useEffect, useReducer, useState } from 'react'
import { createSampleData, nextTicketId } from './data'
import type { Escalation, NewTicketInput, Ticket } from './types'

// Estado del módulo, en memoria (se pierde al recargar). Para conectarlo a services/incidents,
// cambia el cuerpo de estas acciones por llamadas a la API en src/api/; los componentes no cambian.

interface TicketsState {
  tickets: Ticket[]
  escalations: Escalation[]
}

type Action =
  | { type: 'escalate'; ticketId: string; at: string }
  | { type: 'close'; ticketId: string; at: string }
  | { type: 'create'; ticket: Ticket }
  | { type: 'markCalled'; escalationId: string; at: string }

function ticketsReducer(state: TicketsState, action: Action): TicketsState {
  switch (action.type) {
    case 'escalate': {
      const ticket = state.tickets.find((item) => item.id === action.ticketId)
      if (!ticket || ticket.status !== 'abierto' || ticket.level === 3) return state
      const level = ticket.level === 1 ? 2 : 3
      const escalation: Escalation = {
        id: `ESC-${ticket.id}-${level}`,
        ticketId: ticket.id,
        level,
        escalatedAt: action.at,
      }
      return {
        tickets: state.tickets.map((item): Ticket =>
          item.id === ticket.id ? { ...item, level } : item,
        ),
        escalations: [escalation, ...state.escalations],
      }
    }
    case 'close':
      return {
        tickets: state.tickets.map((item): Ticket =>
          item.id === action.ticketId && item.status === 'abierto'
            ? { ...item, status: 'cerrado', closedAt: action.at }
            : item,
        ),
        // Al cerrar el caso se retiran sus avisos de llamada que seguían pendientes.
        escalations: state.escalations.filter(
          (escalation) => escalation.ticketId !== action.ticketId || escalation.calledAt,
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

/** Tickets y escalamientos de Incidentes con sus acciones: escalar, cerrar, crear y marcar llamada. */
export function useTickets() {
  const [state, dispatch] = useReducer(ticketsReducer, undefined, () => createSampleData())

  /** Sube el caso un nivel y devuelve el nivel nuevo, o `null` si ya no se puede escalar. */
  function escalate(ticketId: string) {
    const ticket = state.tickets.find((item) => item.id === ticketId)
    if (!ticket || ticket.status !== 'abierto' || ticket.level === 3) return null
    dispatch({ type: 'escalate', ticketId, at: new Date().toISOString() })
    return ticket.level === 1 ? 2 : 3
  }

  /** Cierra el caso y devuelve cuántos avisos de llamada pendientes se retiraron. */
  function close(ticketId: string) {
    const pending = state.escalations.filter(
      (escalation) => escalation.ticketId === ticketId && !escalation.calledAt,
    ).length
    dispatch({ type: 'close', ticketId, at: new Date().toISOString() })
    return pending
  }

  /** Registra un caso nuevo en el Nivel 1 y devuelve su ID. */
  function create(input: NewTicketInput) {
    const ticket: Ticket = {
      ...input,
      id: nextTicketId(state.tickets),
      createdAt: new Date().toISOString(),
      status: 'abierto',
      level: 1,
    }
    dispatch({ type: 'create', ticket })
    return ticket.id
  }

  function markCalled(escalationId: string) {
    dispatch({ type: 'markCalled', escalationId, at: new Date().toISOString() })
  }

  return { ...state, escalate, close, create, markCalled }
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
