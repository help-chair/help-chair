import { useCallback, useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Clock,
  Filter,
  Info,
  Search,
  ShieldAlert,
  X,
} from 'lucide-react'
import { mensajeDeError } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cargarEventos } from './api'
import { DESTINO_LABEL, ESTADO_LABEL, TIPO_BADGE, TIPO_LABEL, hora } from './data'
import type { EventListItem, EventType } from './types'

type Filtro = EventType | 'all'
type EstadoCarga = 'cargando' | 'lista' | 'error'

export function EventsPage() {
  const [eventos, setEventos] = useState<EventListItem[]>([])
  const [carga, setCarga] = useState<EstadoCarga>('cargando')
  const [errorCarga, setErrorCarga] = useState('')
  const [filtro, setFiltro] = useState<Filtro>('all')
  const [busqueda, setBusqueda] = useState('')

  const cargar = useCallback(() => {
    setCarga('cargando')
    cargarEventos({ ordering: '-last_seen_at' }).then(
      (nuevos) => {
        setEventos(nuevos)
        setCarga('lista')
      },
      (error: unknown) => {
        setErrorCarga(
          mensajeDeError(error, 'Verifica tu conexión con el servicio de Eventos.'),
        )
        setCarga('error')
      },
    )
  }, [])

  useEffect(() => {
    cargar()
  }, [cargar])

  const filtrados = eventos.filter((evt) => {
    const coincideFiltro = filtro === 'all' || evt.event_type === filtro
    const texto = busqueda.trim().toLowerCase()
    const coincideBusqueda =
      !texto ||
      evt.title.toLowerCase().includes(texto) ||
      evt.id.toLowerCase().includes(texto) ||
      (evt.service_code ?? '').toLowerCase().includes(texto)
    return coincideFiltro && coincideBusqueda
  })

  const conteo = (tipo: EventType) => eventos.filter((e) => e.event_type === tipo).length

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
              Gestión de Eventos y Monitoreo (Monitoring &amp; Event Management)
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

      {carga === 'cargando' && (
        <div className="rounded-xl border border-border bg-white p-8 text-center text-sm text-slate-500">
          Cargando eventos…
        </div>
      )}

      {carga === 'error' && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700"
        >
          <p className="font-semibold">No se pudieron cargar los eventos.</p>
          <p className="mt-1 text-xs text-red-700">{errorCarga}</p>
          <Button size="sm" variant="outline" className="mt-3" onClick={cargar}>
            Reintentar
          </Button>
        </div>
      )}

      {carga === 'lista' && (
        <>
          {/* Contadores por Severidad */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button
              onClick={() => setFiltro('all')}
              className={`p-4 rounded-xl border text-left transition-all ${
                filtro === 'all'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-md'
                  : 'bg-white text-slate-700 border-border hover:bg-slate-50'
              }`}
            >
              <p className="text-xs font-semibold uppercase opacity-75">Todos los Eventos</p>
              <p className="text-2xl font-bold mt-1">{eventos.length}</p>
            </button>

            <button
              onClick={() => setFiltro('INFORMATION')}
              className={`p-4 rounded-xl border text-left transition-all ${
                filtro === 'INFORMATION'
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md'
                  : 'bg-white text-slate-700 border-border hover:bg-blue-50/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase opacity-75">Informativos</p>
                <Info size={16} />
              </div>
              <p className="text-2xl font-bold mt-1">{conteo('INFORMATION')}</p>
            </button>

            <button
              onClick={() => setFiltro('WARNING')}
              className={`p-4 rounded-xl border text-left transition-all ${
                filtro === 'WARNING'
                  ? 'bg-amber-600 text-white border-amber-600 shadow-md'
                  : 'bg-white text-slate-700 border-border hover:bg-amber-50/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase opacity-75">Advertencias</p>
                <AlertTriangle size={16} />
              </div>
              <p className="text-2xl font-bold mt-1">{conteo('WARNING')}</p>
            </button>

            <button
              onClick={() => setFiltro('EXCEPTION')}
              className={`p-4 rounded-xl border text-left transition-all ${
                filtro === 'EXCEPTION'
                  ? 'bg-red-600 text-white border-red-600 shadow-md'
                  : 'bg-white text-slate-700 border-border hover:bg-red-50/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase opacity-75">Excepciones</p>
                <ShieldAlert size={16} />
              </div>
              <p className="text-2xl font-bold mt-1">{conteo('EXCEPTION')}</p>
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
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  placeholder="Buscar por ID, descripción o servicio…"
                  className="w-full pl-9 pr-4 py-2 text-sm border border-border rounded-lg bg-surface focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Filter size={14} />
                <span>
                  Mostrando {filtrados.length} de {eventos.length} eventos
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
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
                  {filtrados.map((evt) => (
                    <tr key={evt.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-xs font-semibold text-slate-700 block">
                          {evt.id.slice(0, 8)}
                        </span>
                        <span className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                          <Clock size={12} /> {hora(evt.last_seen_at)}
                          {evt.occurrence_count > 1 && <span>· ×{evt.occurrence_count}</span>}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={TIPO_BADGE[evt.event_type]}>
                          {evt.event_type === 'EXCEPTION' && <AlertTriangle size={12} />}
                          {TIPO_LABEL[evt.event_type]}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <p className="font-medium text-slate-800">{evt.title}</p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                        {evt.origin === 'SYSTEM' ? 'Sistema' : 'Usuario'}
                        {evt.service_code ? ` · ${evt.service_code}` : ''}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {evt.destination ? (
                          <Badge variant="request">{DESTINO_LABEL[evt.destination]}</Badge>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant="outline">{ESTADO_LABEL[evt.state]}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filtrados.length === 0 && (
              <div className="flex flex-col items-center gap-2 p-10 text-center">
                <X size={24} className="text-slate-400" aria-hidden="true" />
                <p className="text-sm font-semibold text-slate-800">No se encontraron eventos</p>
                <p className="text-sm text-slate-600">Ajusta los filtros o la búsqueda.</p>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
