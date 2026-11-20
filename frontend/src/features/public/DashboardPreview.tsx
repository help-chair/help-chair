import {
  Activity,
  AlertTriangle,
  Flame,
  Inbox,
  LayoutDashboard,
  Lock,
  ShieldAlert,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { getRuntimeConfig } from '@/config/runtime'

const KPIS = [
  {
    label: 'Eventos',
    value: '128',
    tone: 'text-slate-800',
    icon: Activity,
    bg: 'bg-blue-50 text-blue-600',
  },
  {
    label: 'Incidencias',
    value: '4',
    tone: 'text-red-600',
    icon: Flame,
    bg: 'bg-red-50 text-red-600',
  },
  {
    label: 'Peticiones',
    value: '18',
    tone: 'text-slate-800',
    icon: Inbox,
    bg: 'bg-purple-50 text-purple-700',
  },
]

const EVENTS = [
  { id: 'EVT-1049', text: 'Timeout en el gateway de pagos', type: 'exception' as const },
  { id: 'EVT-1048', text: 'Disco al 85 % en bd-cluster-02', type: 'warning' as const },
  { id: 'EVT-1047', text: 'Solicitud de VPN · nuevo colaborador', type: 'info' as const },
]

const TYPE_LABEL = { exception: 'Excepción', warning: 'Advertencia', info: 'Informativo' }

/** Ilustración del Service Desk: lo primero que ve el cliente al entrar (dashboard de eventos). */
export function DashboardPreview() {
  const host = `acme.${getRuntimeConfig().baseDomain}`

  return (
    <figure
      role="img"
      aria-label={`Vista previa del dashboard de eventos de una empresa en ${host}`}
      className="w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl"
    >
      <div aria-hidden="true">
        {/* Barra del navegador */}
        <div className="flex items-center gap-3 border-b border-slate-200 bg-slate-100 px-4 py-2.5">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
          </div>
          <div className="flex flex-1 items-center gap-1.5 truncate rounded-md bg-white px-3 py-1 text-xs text-slate-500">
            <Lock size={11} className="shrink-0" />
            <span className="truncate">{host}</span>
          </div>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="hidden w-36 shrink-0 space-y-1 bg-slate-900 p-3 sm:block">
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600 text-[10px] font-bold text-white">
                HC
              </span>
              <span className="text-xs font-semibold text-white">Acme</span>
            </div>
            {[
              { icon: LayoutDashboard, label: 'Dashboard', active: true },
              { icon: Activity, label: 'Eventos' },
              { icon: Inbox, label: 'Peticiones' },
              { icon: Flame, label: 'Incidencias' },
              { icon: ShieldAlert, label: 'Problemas' },
            ].map((item) => (
              <div
                key={item.label}
                className={
                  item.active
                    ? 'flex items-center gap-2 rounded-md bg-indigo-600 px-2 py-1.5 text-[11px] font-medium text-white'
                    : 'flex items-center gap-2 rounded-md px-2 py-1.5 text-[11px] text-slate-400'
                }
              >
                <item.icon size={12} />
                {item.label}
              </div>
            ))}
          </div>

          {/* Contenido */}
          <div className="min-w-0 flex-1 space-y-3 bg-slate-50 p-3 sm:p-4">
            <div className="rounded-lg bg-gradient-to-r from-indigo-700 to-slate-900 px-3 py-2.5 text-white">
              <p className="text-xs font-semibold">Portal Unificado de Gestión de Servicios</p>
              <p className="text-[10px] text-indigo-100">
                Eventos clasificados y enrutados en tiempo real
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {KPIS.map((kpi) => (
                <div
                  key={kpi.label}
                  className="flex items-center justify-between gap-1 rounded-lg border border-slate-200 bg-white p-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-[9px] font-semibold uppercase text-slate-500">
                      {kpi.label}
                    </p>
                    <p className={`text-base font-bold ${kpi.tone}`}>{kpi.value}</p>
                  </div>
                  <span className={`hidden rounded-md p-1.5 sm:block ${kpi.bg}`}>
                    <kpi.icon size={12} />
                  </span>
                </div>
              ))}
            </div>

            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <p className="border-b border-slate-100 px-3 py-2 text-[11px] font-semibold text-slate-700">
                Monitor de eventos
              </p>
              <ul className="divide-y divide-slate-100">
                {EVENTS.map((event) => (
                  <li key={event.id} className="flex items-center gap-2 px-3 py-2">
                    <span className="font-mono text-[10px] font-semibold text-slate-500">
                      {event.id}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-[11px] text-slate-700">
                      {event.text}
                    </span>
                    <Badge variant={event.type} className="shrink-0 px-2 py-0 text-[10px]">
                      {event.type !== 'info' && <AlertTriangle size={10} />}
                      {TYPE_LABEL[event.type]}
                    </Badge>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </figure>
  )
}
