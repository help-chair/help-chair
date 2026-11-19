import { Shield, Users, Settings, Activity } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      {/* Banner de Administrador */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-600/30 text-indigo-400 rounded-lg">
              <Shield size={20} />
            </span>
            <h3 className="text-xl font-bold">Panel de Control de Administración</h3>
          </div>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Visión global del stack Help Chair: gestión de roles y accesos, configuración de la empresa,
            auditoría de eventos de seguridad y control de SLAs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs text-white border-white/20">
            Rol: Administrador
          </Badge>
        </div>
      </div>

      {/* Métricas clave de administración */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Cuentas y Accesos</p>
            <Users size={18} className="text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">6 Usuarios</p>
          <p className="text-xs text-slate-500 mt-1">Directorio activo de la organización</p>
        </Card>

        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Eventos de Seguridad</p>
            <Activity size={18} className="text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">0 Alertas Críticas</p>
          <p className="text-xs text-slate-500 mt-1">Monitoreo continuo de autenticación</p>
        </Card>

        <Card className="p-5 bg-white border-border">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-slate-500">Cumplimiento de SLA</p>
            <Settings size={18} className="text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mt-2">99.4%</p>
          <p className="text-xs text-slate-500 mt-1">Respeto de tiempos en peticiones e incidencias</p>
        </Card>
      </div>
    </div>
  )
}
