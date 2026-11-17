import { useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Clock,
  Filter,
  Info,
  Search,
  ShieldAlert,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { INITIAL_EVENTS } from './data'
import type { EventSeverity } from './types'

export function EventsPage() {
  const [filter, setFilter] = useState<EventSeverity | 'all'>('all')
  const [search, setSearch] = useState('')

  const filteredEvents = INITIAL_EVENTS.filter((evt) => {
    const matchesFilter = filter === 'all' || evt.type === filter
    const matchesSearch =
      search === '' ||
      evt.title.toLowerCase().includes(search.toLowerCase()) ||
      evt.source.toLowerCase().includes(search.toLowerCase()) ||
      evt.id.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const countInfo = INITIAL_EVENTS.filter((e) => e.type === 'informational').length
  const countWarn = INITIAL_EVENTS.filter((e) => e.type === 'warning').length
  const countExc = INITIAL_EVENTS.filter((e) => e.type === 'exception').length

  return (
    <div className="space-y-6">
      {/* Banner de Práctica ITIL */}
      <div className="bg-white border border-border p-6 rounded-xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Activity size={20} />
            </span>
            <h3 className="text-xl font-bold text-slate-900">
              Gestión de Eventos y Monitoreo (Monitoring & Event Management)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1 max-w-3xl">
            Punto de entrada y correlación del stack. Clasifica y enruta señales operacionales según
            las 9 reglas ITIL v4 hacia Incidencias, Peticiones o Problemas.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            Motor de Reglas v1
          </Badge>
        </div>
      </div>

      {/* Contadores por Severidad */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <button
          onClick={() => setFilter('all')}
          className={`p-4 rounded-xl border text-left transition-all ${
            filter === 'all'
              ? 'bg-slate-900 text-white border-slate-900 shadow-md'
              : 'bg-white text-slate-700 border-border hover:bg-slate-50'
          }`}
        >
          <p className="text-xs font-semibold uppercase opacity-75">Todos los Eventos</p>
          <p className="text-2xl font-bold mt-1">{INITIAL_EVENTS.length}</p>
        </button>

        <button
          onClick={() => setFilter('informational')}
          className={`p-4 rounded-xl border text-left transition-all ${
            filter === 'informational'
              ? 'bg-blue-600 text-white border-blue-600 shadow-md'
              : 'bg-white text-slate-700 border-border hover:bg-blue-50/50'
          }`}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase opacity-75">Informativos</p>
            <Info size={16} />
          </div>
          <p className="text-2xl font-bold mt-1">{countInfo}</p>
        </button>

        <button
          onClick={() => setFilter('warning')}
          className={`p-4 rounded-xl border text-left transition-all ${
            filter === 'warning'
              ? 'bg-amber-600 text-white border-amber-600 shadow-md'
              : 'bg-white text-slate-700 border-border hover:bg-amber-50/50'
          }`}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase opacity-75">Advertencias</p>
            <AlertTriangle size={16} />
          </div>
          <p className="text-2xl font-bold mt-1">{countWarn}</p>
        </button>

        <button
          onClick={() => setFilter('exception')}
          className={`p-4 rounded-xl border text-left transition-all ${
            filter === 'exception'
              ? 'bg-red-600 text-white border-red-600 shadow-md'
              : 'bg-white text-slate-700 border-border hover:bg-red-50/50'
          }`}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase opacity-75">Excepciones</p>
            <ShieldAlert size={16} />
          </div>
          <p className="text-2xl font-bold mt-1">{countExc}</p>
        </button>
      </div>

      {/* Tabla y Filtros */}
      <Card className="overflow-hidden">
        <div className="p-4 border-b border-border flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por ID, descripción o componente..."
              className="w-full pl-9 pr-4 py-2 text-sm border border-border rounded-lg bg-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Filter size={14} />
            <span>
              Mostrando {filteredEvents.length} de {INITIAL_EVENTS.length} eventos
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase border-b border-border">
              <tr>
                <th className="px-6 py-3 font-semibold">ID / Hora</th>
                <th className="px-6 py-3 font-semibold">Tipo ITIL</th>
                <th className="px-6 py-3 font-semibold">Descripción del Evento</th>
                <th className="px-6 py-3 font-semibold">Componente Origen</th>
                <th className="px-6 py-3 font-semibold">Destino de Enrutamiento</th>
                <th className="px-6 py-3 font-semibold">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-mono text-xs font-semibold text-slate-700 block">
                      {evt.id}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                      <Clock size={12} /> {evt.timestamp}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {evt.type === 'exception' && (
                      <Badge variant="exception">
                        <AlertTriangle size={12} /> Excepción
                      </Badge>
                    )}
                    {evt.type === 'warning' && (
                      <Badge variant="warning">
                        <AlertTriangle size={12} /> Advertencia
                      </Badge>
                    )}
                    {evt.type === 'informational' && <Badge variant="info">Informativo</Badge>}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-medium text-slate-800">{evt.title}</p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                    {evt.source}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant="request">{evt.destination}</Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant="outline">{evt.status}</Badge>
                  </td>
                </tr>
              ))}
              {filteredEvents.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-sm text-slate-400">
                    No se encontraron eventos con los filtros aplicados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
