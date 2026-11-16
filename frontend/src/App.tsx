import { useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Bell,
  BookOpen,
  CheckCircle2,
  Clock,
  ExternalLink,
  Flame,
  Inbox,
  LayoutDashboard,
  LifeBuoy,
  Server,
  ShieldAlert,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { RequestsPage } from '@/features/requests/RequestsPage'

interface EventItem {
  id: string
  timestamp: string
  type: 'informational' | 'warning' | 'exception'
  title: string
  source: string
  destination: string
  status: string
}

const mockEvents: EventItem[] = [
  {
    id: 'EVT-1049',
    timestamp: '11:15:02',
    type: 'exception',
    title: 'Fallo de conexión en Gateway de Pagos - Timeout > 5000ms',
    source: 'Infraestructura / API',
    destination: 'Incidencias (P1 - Crítico)',
    status: 'Enrutado a Incidencias',
  },
  {
    id: 'EVT-1048',
    timestamp: '11:10:45',
    type: 'warning',
    title: 'Espacio en disco > 85% en nodo de base de datos bd-cluster-02',
    source: 'Monitoring Agent',
    destination: 'Registro y vigilancia',
    status: 'Bajo observación',
  },
  {
    id: 'EVT-1047',
    timestamp: '11:02:18',
    type: 'informational',
    title: 'Solicitud de acceso a VPN para nuevo colaborador',
    source: 'Portal de autoservicio',
    destination: 'Peticiones (Catálogo)',
    status: 'Enrutado a Peticiones',
  },
  {
    id: 'EVT-1046',
    timestamp: '10:55:00',
    type: 'informational',
    title: 'Copia de seguridad incremental completada satisfactoriamente',
    source: 'Cron Backup Service',
    destination: 'Solo registro',
    status: 'Cerrado automático',
  },
  {
    id: 'EVT-1045',
    timestamp: '10:48:12',
    type: 'exception',
    title: 'Intentos fallidos de autenticación reiterados (5 intentos en 1 min)',
    source: 'Servicio de Accesos',
    destination: 'Seguridad / Accesos',
    status: 'Enrutado a Accesos',
  },
]

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'events' | 'requests'>('dashboard')

  return (
    <div className="flex h-screen bg-slate-100 text-slate-800">
      {/* Sidebar de navegación */}
      <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col justify-between shadow-xl">
        <div>
          {/* Logo y contexto de la empresa */}
          <div className="p-5 border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md">
                HC
              </div>
              <div>
                <h1 className="font-bold text-base text-white tracking-wide">Help Chair</h1>
                <p className="text-xs text-slate-400">ITIL v4 Service Desk</p>
              </div>
            </div>
            <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-indigo-300 border border-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              {window.location.host}
            </div>
          </div>

          {/* Menú principal */}
          <nav className="p-4 space-y-1">
            <p className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Centro de Mando
            </p>
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'dashboard'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <LayoutDashboard size={18} />
              Dashboard Principal
            </button>
            <button
              onClick={() => setActiveTab('events')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'events'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Activity size={18} />
              Gestión de Eventos
              <span className="ml-auto bg-slate-800 text-slate-300 text-xs px-2 py-0.5 rounded-full">
                5
              </span>
            </button>

            <p className="pt-4 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Microservicios ITIL
            </p>
            <a
              href="#incidents"
              className="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <div className="flex items-center gap-3">
                <Flame size={18} className="text-red-400" />
                <span>Incidencias</span>
              </div>
              <ExternalLink size={14} className="text-slate-500" />
            </a>
            <button
              onClick={() => setActiveTab('requests')}
              aria-current={activeTab === 'requests' ? 'page' : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'requests'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Inbox size={18} className={activeTab === 'requests' ? '' : 'text-purple-400'} />
              Peticiones
            </button>
            <a
              href="#problems"
              className="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <div className="flex items-center gap-3">
                <ShieldAlert size={18} className="text-amber-400" />
                <span>Problemas</span>
              </div>
              <ExternalLink size={14} className="text-slate-500" />
            </a>
            <a
              href="#knowledge"
              className="flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <div className="flex items-center gap-3">
                <BookOpen size={18} className="text-emerald-400" />
                <span>Base de Conocimiento</span>
              </div>
              <ExternalLink size={14} className="text-slate-500" />
            </a>
          </nav>
        </div>

        {/* Footer del sidebar */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-3 py-2 text-sm text-slate-400">
            <Server size={16} />
            <span className="text-xs">Stack: K8s Namespace Activo</span>
          </div>
        </div>
      </aside>

      {/* Contenido Principal */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        {/* Header superior */}
        <header className="h-16 bg-white border-b border-border px-8 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-800">
              {activeTab === 'dashboard'
                ? 'Service Desk · Vista Operativa'
                : activeTab === 'requests'
                  ? 'Gestión de Peticiones'
                  : 'Consola de Monitoreo de Eventos'}
            </h2>
            <Badge variant="outline">Gateway del Stack</Badge>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-surface-muted rounded-full transition-colors">
              <Bell size={18} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white"></span>
            </button>
            <div className="flex items-center gap-2 pl-4 border-l border-border">
              <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center font-medium text-xs">
                AD
              </div>
              <div className="text-left text-xs">
                <p className="font-semibold text-slate-700">Admin Help Desk</p>
                <p className="text-slate-500">Service Desk Lead</p>
              </div>
            </div>
          </div>
        </header>

        {activeTab === 'requests' && <RequestsPage />}

        {/* Cuerpo del Dashboard */}
        <div className="p-8 max-w-7xl mx-auto w-full space-y-6" hidden={activeTab === 'requests'}>
          {/* Banner de bienvenida / Estado */}
          <div className="bg-gradient-to-r from-indigo-700 to-slate-900 rounded-xl p-6 text-white shadow-sm flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="text-xl font-bold">Portal Unificado de Gestión de Servicios</h3>
              <p className="text-sm text-indigo-100 max-w-2xl">
                Monitorea en tiempo real los eventos de infraestructura y solicitudes de usuarios.
                El enrutamiento automático ITIL v4 clasifica eventos hacia Peticiones, Incidencias o
                Problemas.
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="primary" size="sm" className="bg-indigo-600 hover:bg-indigo-500">
                <LifeBuoy size={16} />
                Nuevo Ticket Manual
              </Button>
            </div>
          </div>

          {/* Tarjetas de Métricas ITIL con el componente Card */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Tarjeta 1: Eventos */}
            <Card className="p-5 flex items-center justify-between">
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
            <Card className="p-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase text-slate-500">
                  Incidencias Abiertas
                </p>
                <p className="text-2xl font-bold text-red-600 mt-1">4</p>
                <p className="text-xs text-slate-500 mt-1">1 P1 Crítica activa</p>
              </div>
              <div className="p-3 bg-red-50 text-red-600 rounded-lg">
                <Flame size={24} />
              </div>
            </Card>

            {/* Tarjeta 3: Peticiones */}
            <Card className="p-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase text-slate-500">
                  Peticiones de Servicio
                </p>
                <p className="text-2xl font-bold text-slate-800 mt-1">18</p>
                <p className="text-xs text-blue-600 font-medium mt-1">3 en aprobación</p>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
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

          {/* Tabla de Gestión de Eventos y Enrutamiento (Live Feed) */}
          <Card className="overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-slate-800">
                  Flujo de Eventos Recientes (Monitoring Feed)
                </h4>
                <p className="text-xs text-slate-500">
                  Visualización del Gateway de Eventos y enrutamiento hacia microservicios.
                </p>
              </div>
              <Badge variant="default">Reglas ITIL v4 Activas</Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 text-xs uppercase border-b border-border">
                  <tr>
                    <th className="px-6 py-3 font-semibold">ID / Hora</th>
                    <th className="px-6 py-3 font-semibold">Tipo ITIL</th>
                    <th className="px-6 py-3 font-semibold">Descripción del Evento</th>
                    <th className="px-6 py-3 font-semibold">Origen</th>
                    <th className="px-6 py-3 font-semibold">Destino de Enrutamiento</th>
                    <th className="px-6 py-3 font-semibold">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {mockEvents.map((evt) => (
                    <tr key={evt.id} className="hover:bg-slate-50 transition-colors">
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
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </main>
    </div>
  )
}
