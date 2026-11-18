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

/**
 * Módulo de Incidencias (Equipo 4 · Incident Management), según el diseño en Figma
 * (frontend/docs/incidents/). Trabaja con datos de ejemplo en memoria hasta que
 * services/incidents publique su API (contracts/incidents/openapi.yaml).
 */
export function IncidentsPage() {
  const { tickets, escalations, escalate, close, create, markCalled } = useTickets()
  const now = useNow()
  const [modalOpen, setModalOpen] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [highlightId, setHighlightId] = useState<string | null>(null)

  function handleEscalate(ticketId: string) {
    const level = escalate(ticketId)
    if (level) {
      setNotice(
        `${ticketId} escaló a Nivel ${level}: Incidentes debe llamar ${CALL_TARGET[level]}.`,
      )
    }
  }

  function handleClose(ticketId: string) {
    const removed = close(ticketId)
    setNotice(
      removed > 0
        ? `${ticketId} quedó cerrado y se retiraron sus avisos de llamada pendientes.`
        : `${ticketId} quedó cerrado.`,
    )
  }

  function handleMarkCalled(escalation: Escalation) {
    markCalled(escalation.id)
    setNotice(`Se registró la llamada por ${escalation.ticketId} (Nivel ${escalation.level}).`)
  }

  function handleCreate(input: NewTicketInput) {
    const id = create(input)
    setModalOpen(false)
    setHighlightId(id)
    setNotice(`Ticket ${id} creado. Aparece al inicio de la tabla.`)
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

      <MetricsRow metrics={computeMetrics(tickets, now)} />
      <TicketTable
        tickets={tickets}
        highlightId={highlightId}
        onEscalate={handleEscalate}
        onClose={handleClose}
      />
      <EscalationPanel escalations={escalations} now={now} onMarkCalled={handleMarkCalled} />
      <NewTicketModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}
