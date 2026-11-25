import { useState } from 'react'
import { Info, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { CALL_TARGET, computeMetrics } from './data'
import { EscalationPanel } from './EscalationPanel'
import { MetricsRow } from './MetricsRow'
import { NewTicketModal } from './NewTicketModal'
import { TicketTable } from './TicketTable'
import type { Escalation, NewTicketInput } from './types'
import { useNow, useTickets } from './useTickets'

interface IncidentsPageProps {
  /** ID del agente de la sesión: se asigna como responsable al cerrar un incidente sin agente. */
  agenteId?: string
}

/**
 * Módulo de Incidencias (Equipo 4 · Incident Management), según el diseño en Figma
 * (frontend/docs/incidents/). Lee y modifica los incidentes en services/incidents
 * (contracts/incidents/openapi.yaml).
 */
export function IncidentsPage({ agenteId }: IncidentsPageProps) {
  const { tickets, escalations, carga, errorCarga, recargar, escalate, close, create, markCalled } =
    useTickets()
  const now = useNow()
  const [modalOpen, setModalOpen] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [highlightId, setHighlightId] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  async function handleEscalate(ticketId: string) {
    setBusyId(ticketId)
    const resultado = await escalate(ticketId)
    setBusyId(null)
    setNotice(
      resultado.ok
        ? `${ticketId} escaló a Nivel ${resultado.valor}: Incidentes debe llamar ${CALL_TARGET[resultado.valor as Escalation['level']]}.`
        : `No se pudo escalar ${ticketId}: ${resultado.detalle}`,
    )
  }

  async function handleClose(ticketId: string) {
    setBusyId(ticketId)
    const resultado = await close(ticketId, agenteId)
    setBusyId(null)
    if (!resultado.ok) {
      setNotice(`No se pudo cerrar ${ticketId}: ${resultado.detalle}`)
      return
    }
    setNotice(
      resultado.valor > 0
        ? `${ticketId} quedó cerrado y se retiraron sus avisos de llamada pendientes.`
        : `${ticketId} quedó cerrado.`,
    )
  }

  function handleMarkCalled(escalation: Escalation) {
    markCalled(escalation.id)
    setNotice(`Se registró la llamada por ${escalation.ticketId} (Nivel ${escalation.level}).`)
  }

  async function handleCreate(input: NewTicketInput): Promise<string | null> {
    const resultado = await create(input)
    if (!resultado.ok) return resultado.detalle
    setModalOpen(false)
    setHighlightId(resultado.valor)
    setNotice(`Ticket ${resultado.valor} creado. Aparece al inicio de la tabla.`)
    return null
  }

  return (
    // `relative` mantiene los controles sr-only (posición absoluta) dentro del área con scroll.
    <div className="relative space-y-6">
      <section
        aria-labelledby="incidentes-titulo"
        className="flex flex-col gap-4 rounded-xl bg-gradient-to-r from-indigo-700 via-indigo-800 to-slate-900 p-6 text-white shadow-sm md:flex-row md:items-center md:justify-between"
      >
        <div className="max-w-3xl space-y-1">
          <h3 id="incidentes-titulo" className="text-xl font-bold">
            Gestión de Incidentes
          </h3>
          <p className="text-sm text-indigo-100">
            Revisa los tickets abiertos y cerrados, su categorización por urgencia, prioridad e
            impacto, y el nivel de escalamiento. Si un nivel no puede resolverlo, Incidentes recibe
            un aviso para llamar a un cargo mayor.
          </p>
        </div>
        <Button
          variant="outline"
          className="shrink-0 border-white/30 bg-white/10 text-white hover:bg-white/20"
          onClick={() => setModalOpen(true)}
        >
          <Plus size={16} aria-hidden="true" />
          Nuevo ticket
        </Button>
      </section>

      {/* Región viva siempre presente para que los lectores de pantalla anuncien cada acción. */}
      <div role="status" className={cn(!notice && 'sr-only')}>
        {notice && (
          <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-700">
            <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
            <p className="flex-1">{notice}</p>
            <button
              type="button"
              aria-label="Cerrar aviso"
              onClick={() => setNotice(null)}
              className="rounded p-0.5 hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>

      {carga === 'cargando' && (
        <div className="rounded-xl border border-border bg-white p-8 text-center text-sm text-slate-500">
          Cargando incidentes…
        </div>
      )}

      {carga === 'error' && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700"
        >
          <p className="font-semibold">No se pudieron cargar los incidentes.</p>
          <p className="mt-1 text-xs text-red-700">{errorCarga}</p>
          <Button size="sm" variant="outline" className="mt-3" onClick={recargar}>
            Reintentar
          </Button>
        </div>
      )}

      {carga === 'lista' && (
        <>
          <MetricsRow metrics={computeMetrics(tickets, now)} />
          <TicketTable
            tickets={tickets}
            highlightId={highlightId}
            busyId={busyId}
            onEscalate={(ticketId) => void handleEscalate(ticketId)}
            onClose={(ticketId) => void handleClose(ticketId)}
          />
          <EscalationPanel escalations={escalations} now={now} onMarkCalled={handleMarkCalled} />
        </>
      )}
      <NewTicketModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}
