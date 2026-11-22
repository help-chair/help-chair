import { AlertTriangle, Flame, Layers, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import type { TabKey } from '@/components/layout/ServiceDeskLayout'

interface N2AreaPanelProps {
  onNavigate: (tab: TabKey) => void
}

/**
 * Bloque del Agente N2 dentro del dashboard principal: incidentes escalados,
 * investigación de problemas y servicios afectados, con accesos rápidos.
 */
export function N2AreaPanel({ onNavigate }: N2AreaPanelProps) {
  return (
    <section aria-labelledby="n2-panel-titulo" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="p-2 bg-red-50 text-red-600 rounded-lg">
            <Flame size={18} aria-hidden="true" />
          </span>
          <div>
            <h3 id="n2-panel-titulo" className="text-base font-semibold text-slate-900">
              Panel de Área Operativa (Especialista N2)
            </h3>
            <p className="text-xs text-slate-500">
              Incidentes escalados y problemas asignados a tu área de especialidad.
            </p>
          </div>
        </div>
        <Badge variant="outline">Rol: Agente N2 / Owner</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Incidentes Escalados N2</p>
            <Flame size={18} className="text-red-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">2 Activos</p>
          <p className="text-xs text-slate-500 mt-1">Requieren atención técnica especializada</p>
        </Card>

        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Investigación de Problemas</p>
            <AlertTriangle size={18} className="text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">1 En Análisis</p>
          <p className="text-xs text-slate-500 mt-1">Causa raíz pendiente de identificación</p>
        </Card>

        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Servicios Afectados</p>
            <Layers size={18} className="text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">Sistemas & BD</p>
          <p className="text-xs text-slate-500 mt-1">Componentes en monitoreo activo</p>
        </Card>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" size="md" onClick={() => onNavigate('incidents')}>
          <Flame size={16} aria-hidden="true" />
          Gestionar Incidencias
        </Button>
        <Button variant="secondary" size="md" onClick={() => onNavigate('problems')}>
          <ShieldAlert size={16} aria-hidden="true" />
          Gestionar Problemas
        </Button>
      </div>
    </section>
  )
}
