import { Flame, Headset, Inbox, Timer } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import type { TabKey } from '@/components/layout/ServiceDeskLayout'

interface N1AreaPanelProps {
  onNavigate: (tab: TabKey) => void
}

/**
 * Bloque del Agente N1 (primera línea) dentro del dashboard principal:
 * cola de incidencias y peticiones de la mesa de ayuda, con accesos rápidos.
 * Métricas de ejemplo mientras los backends no publiquen su API.
 */
export function N1AreaPanel({ onNavigate }: N1AreaPanelProps) {
  return (
    <section aria-labelledby="n1-panel-titulo" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
            <Headset size={18} aria-hidden="true" />
          </span>
          <div>
            <h3 id="n1-panel-titulo" className="text-base font-semibold text-slate-900">
              Panel de Primera Línea (Agente N1)
            </h3>
            <p className="text-xs text-slate-500">
              Cola de incidencias y peticiones de la mesa de ayuda.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">Rol: Agente N1 / Mesa de ayuda</Badge>
          <Badge variant="outline">Vista previa · datos simulados</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Incidencias por Atender</p>
            <Flame size={18} className="text-red-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">6 Activas</p>
          <p className="text-xs text-slate-500 mt-1">1 sin clasificar</p>
        </Card>

        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Peticiones por Aprobar</p>
            <Inbox size={18} className="text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">3 Pendientes</p>
          <p className="text-xs text-slate-500 mt-1">2 en provisión</p>
        </Card>

        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">SLA por Vencer</p>
            <Timer size={18} className="text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">1 Hoy</p>
          <p className="text-xs text-slate-500 mt-1">Riesgo bajo en el resto</p>
        </Card>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" size="md" onClick={() => onNavigate('incidents')}>
          <Flame size={16} aria-hidden="true" />
          Atender Incidencias
        </Button>
        <Button variant="secondary" size="md" onClick={() => onNavigate('requests')}>
          <Inbox size={16} aria-hidden="true" />
          Atender Peticiones
        </Button>
      </div>
    </section>
  )
}
