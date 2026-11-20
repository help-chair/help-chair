import { useState } from 'react'
import { ClipboardList, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { REQUEST_STATES, STATUS_BADGE, formatDate, getCategory, getStatus } from './data'
import type { RequestStatus, ServiceRequest } from './types'

interface RequestQueueProps {
  requests: ServiceRequest[]
}

const FILTROS: { id: RequestStatus | 'todas'; label: string }[] = [
  { id: 'todas', label: 'Todas' },
  ...REQUEST_STATES.map((state) => ({ id: state.id, label: state.label })),
]

/**
 * Bandeja de atención de Peticiones (solo lectura) para agentes y administradores.
 * Mientras `services/requests` no publique su API, trabaja con los datos de ejemplo
 * y no permite asignar ni aprobar: esos son campos y reglas del backend.
 */
export function RequestQueue({ requests }: RequestQueueProps) {
  const [status, setStatus] = useState<RequestStatus | 'todas'>('todas')
  const [search, setSearch] = useState('')

  const filtradas = requests.filter((request) => {
    const coincideEstado = status === 'todas' || request.status === status
    const texto = search.trim().toLowerCase()
    const coincideBusqueda =
      !texto ||
      request.id.toLowerCase().includes(texto) ||
      request.serviceName.toLowerCase().includes(texto) ||
      request.requester.toLowerCase().includes(texto) ||
      request.department.toLowerCase().includes(texto)
    return coincideEstado && coincideBusqueda
  })

  return (
    <section aria-labelledby="cola-titulo" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 id="cola-titulo" className="text-base font-semibold text-slate-800">
            Cola de atención
          </h3>
          <p className="text-sm text-slate-600">
            Vista previa con datos simulados, hasta que <code className="font-mono">services/requests</code>{' '}
            publique su API.
          </p>
        </div>
        <Badge variant="outline">Vista previa · datos simulados</Badge>
      </div>

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div role="group" aria-label="Filtrar por estado" className="flex flex-wrap gap-2">
          {FILTROS.map((filtro) => (
            <Button
              key={filtro.id}
              variant={status === filtro.id ? 'primary' : 'ghost'}
              size="sm"
              aria-pressed={status === filtro.id}
              onClick={() => setStatus(filtro.id)}
            >
              {filtro.label}
            </Button>
          ))}
        </div>
        <div className="relative flex-1 max-w-md">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por ID, servicio, solicitante o departamento…"
            aria-label="Buscar en la cola"
            className="w-full rounded-lg border border-border bg-surface py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase border-b border-border">
              <tr>
                <th className="px-6 py-3 font-semibold">ID</th>
                <th className="px-6 py-3 font-semibold">Servicio</th>
                <th className="px-6 py-3 font-semibold">Solicitante</th>
                <th className="px-6 py-3 font-semibold">Departamento</th>
                <th className="px-6 py-3 font-semibold">Fecha</th>
                <th className="px-6 py-3 font-semibold">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtradas.map((request) => {
                const estado = getStatus(request.status)
                const categoria = getCategory(request.category)
                return (
                  <tr key={request.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-3 font-mono text-xs font-semibold text-slate-500">
                      {request.id}
                    </td>
                    <td className="px-6 py-3">
                      <p className="font-medium text-slate-800">{request.serviceName}</p>
                      <p className="text-xs text-slate-400">{categoria.label}</p>
                    </td>
                    <td className="px-6 py-3 text-slate-600">{request.requester}</td>
                    <td className="px-6 py-3 text-slate-600">{request.department}</td>
                    <td className="px-6 py-3 text-xs text-slate-500">
                      {formatDate(request.createdAt)}
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant={STATUS_BADGE[request.status]}>{estado.label}</Badge>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {filtradas.length === 0 && (
          <div className="flex flex-col items-center gap-2 p-10 text-center">
            <ClipboardList size={24} className="text-slate-400" aria-hidden="true" />
            <p className="text-sm font-semibold text-slate-800">No hay peticiones en esta cola</p>
            <p className={cn('text-sm text-slate-600')}>Ajusta los filtros o la búsqueda.</p>
          </div>
        )}
      </Card>
    </section>
  )
}
