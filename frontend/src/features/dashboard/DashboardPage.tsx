import {
  Activity,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Flame,
  Inbox,
  LifeBuoy,
  ShieldAlert,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { INITIAL_EVENTS } from '@/features/events/data'

interface DashboardPageProps {
  onNavigate: (tab: 'dashboard' | 'events' | 'requests' | 'incidents' | 'problems' | 'knowledge') => void
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const recentEvents = INITIAL_EVENTS.slice(0, 3)

  return (
    <div className="space-y-6">
      {/* Banner de bienvenida / Estado general */}
      <div className="bg-gradient-to-r from-indigo-700 via-indigo-800 to-slate-900 rounded-xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h3 className="text-xl font-bold">Portal Unificado de Gestión de Servicios</h3>
          <p className="text-sm text-indigo-100 max-w-2xl">
            Centro de control ITIL v4. Monitorea eventos de infraestructura en tiempo real y gestiona
            el ciclo de vida de peticiones, incidentes y problemas en tu stack empresarial.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigate('requests')}
            className="bg-indigo-600 hover:bg-indigo-500"
          >
            <LifeBuoy size={16} />
            Catálogo de Servicios
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate('events')}
            className="bg-slate-800/80 hover:bg-slate-800"
          >
            <Activity size={16} />
            Consola de Eventos
          </Button>
        </div>
      </div>

      {/* Tarjetas de Métricas ITIL */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Tarjeta 1: Eventos */}
        <Card
          onClick={() => onNavigate('events')}
          className="p-5 flex items-center justify-between cursor-pointer hover:border-indigo-300 transition-all hover:shadow-md"
        >
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">Eventos (24h)</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">128</p>
            <p className="text-xs text-emerald-600 font-medium mt-1">94% auto-clasificados</p>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Activity size={24} />
          </div>
        </Card>

        {/* Tarjeta 2: Incidencias */}
        <Card
          onClick={() => onNavigate('incidents')}
          className="p-5 flex items-center justify-between cursor-pointer hover:border-red-300 transition-all hover:shadow-md"
        >
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">Incidencias Abiertas</p>
            <p className="text-2xl font-bold text-red-600 mt-1">4</p>
            <p className="text-xs text-slate-500 mt-1">1 P1 Crítica activa</p>
          </div>
          <div className="p-3 bg-red-50 text-red-600 rounded-lg">
            <Flame size={24} />
          </div>
        </Card>

        {/* Tarjeta 3: Peticiones */}
        <Card
          onClick={() => onNavigate('requests')}
          className="p-5 flex items-center justify-between cursor-pointer hover:border-purple-300 transition-all hover:shadow-md"
        >
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">Peticiones de Servicio</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">18</p>
            <p className="text-xs text-purple-600 font-medium mt-1">3 en aprobación</p>
          </div>
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Inbox size={24} />
          </div>
        </Card>

        {/* Tarjeta 4: SLAs */}
        <Card className="p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-500">Cumplimiento SLA</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">98.2%</p>
            <p className="text-xs text-slate-500 mt-1">Meta mensual: 95.0%</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 size={24} />
          </div>
        </Card>
      </div>

      {/* Resumen de Accesos Rápidos y Últimos Eventos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna Izquierda: Acceso Rápido a Microservicios ITIL */}
        <Card className="p-6 space-y-4 lg:col-span-1">
          <h4 className="font-semibold text-slate-900 text-sm uppercase tracking-wider">
            Microservicios del Stack
          </h4>
          <p className="text-xs text-slate-500">
            Navega directamente a los submódulos de gestión de servicios:
          </p>
          <div className="space-y-2">
            <button
              onClick={() => onNavigate('events')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-border hover:bg-slate-50 text-left transition-colors text-sm"
            >
              <div className="flex items-center gap-3">
                <Activity size={18} className="text-blue-600" />
                <span className="font-medium text-slate-800">Gestión de Eventos</span>
              </div>
              <ArrowRight size={16} className="text-slate-400" />
            </button>

            <button
              onClick={() => onNavigate('incidents')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-border hover:bg-slate-50 text-left transition-colors text-sm"
            >
              <div className="flex items-center gap-3">
                <Flame size={18} className="text-red-600" />
                <span className="font-medium text-slate-800">Gestión de Incidencias</span>
              </div>
              <ArrowRight size={16} className="text-slate-400" />
            </button>

            <button
              onClick={() => onNavigate('requests')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-border hover:bg-slate-50 text-left transition-colors text-sm"
            >
              <div className="flex items-center gap-3">
                <Inbox size={18} className="text-purple-600" />
                <span className="font-medium text-slate-800">Gestión de Peticiones</span>
              </div>
              <ArrowRight size={16} className="text-slate-400" />
            </button>

            <button
              onClick={() => onNavigate('problems')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-border hover:bg-slate-50 text-left transition-colors text-sm"
            >
              <div className="flex items-center gap-3">
                <ShieldAlert size={18} className="text-amber-600" />
                <span className="font-medium text-slate-800">Gestión de Problemas</span>
              </div>
              <ArrowRight size={16} className="text-slate-400" />
            </button>

            <button
              onClick={() => onNavigate('knowledge')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-border hover:bg-slate-50 text-left transition-colors text-sm"
            >
              <div className="flex items-center gap-3">
                <BookOpen size={18} className="text-emerald-600" />
                <span className="font-medium text-slate-800">Base de Conocimiento</span>
              </div>
              <ArrowRight size={16} className="text-slate-400" />
            </button>
          </div>
        </Card>

        {/* Columna Derecha: Vista previa del feed de eventos */}
        <Card className="p-6 space-y-4 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-semibold text-slate-900 text-sm uppercase tracking-wider">
                  Eventos Recientes (Live Feed)
                </h4>
                <p className="text-xs text-slate-500">
                  Últimas señales detectadas y clasificadas por el Gateway de Eventos
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('events')}
                className="text-xs"
              >
                Ver consola completa
              </Button>
            </div>

            <div className="space-y-3">
              {recentEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="p-3.5 rounded-lg border border-border bg-slate-50/50 flex items-center justify-between gap-3 text-sm"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-500 font-semibold">
                        {evt.id}
                      </span>
                      <span className="text-xs text-slate-400">• {evt.timestamp}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-medium border border-indigo-100">
                        {evt.destination}
                      </span>
                    </div>
                    <p className="font-medium text-slate-800">{evt.title}</p>
                  </div>
                  <span className="text-xs text-slate-500 shrink-0">{evt.status}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-border flex items-center justify-between text-xs text-slate-400">
            <span>Reglas ITIL v4 de clasificación activas</span>
            <span>Stack Namespace: K8s multiempresa</span>
          </div>
        </Card>
      </div>
    </div>
  )
}
