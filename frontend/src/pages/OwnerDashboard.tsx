import { Flame, AlertTriangle, Layers } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function OwnerDashboard() {
  return (
    <div className="space-y-6">
      {/* Banner de Owner de Área */}
      <div className="bg-gradient-to-r from-red-950 via-slate-900 to-slate-900 rounded-xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-red-600/30 text-red-400 rounded-lg">
              <Flame size={20} />
            </span>
            <h3 className="text-xl font-bold">Panel de Área Operativa (Especialista N2)</h3>
          </div>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Gestión de incidentes críticos y problemas escalados asignados a tu área de especialidad.
            Coordinación de diagnóstico, workaround y causas raíz.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs text-white border-white/20">
            Rol: Agente N2 / Owner
          </Badge>
        </div>
      </div>

      {/* Métricas clave de N2 */}
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
    </div>
  )
}
