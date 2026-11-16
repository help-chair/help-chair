import { AlertTriangle, Clock, Flame, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export function IncidentsPage() {
  return (
    <div className="space-y-6">
      {/* Banner de la Práctica */}
      <div className="bg-white border border-border p-6 rounded-xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-red-50 text-red-600 rounded-lg">
              <Flame size={20} />
            </span>
            <h3 className="text-xl font-bold text-slate-900">
              Gestión de Incidencias (Incident Management)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1 max-w-3xl">
            Práctica ITIL v4: Minimizar el impacto negativo de las interrupciones del servicio
            restaurando la operación normal lo antes posible. Prioridad calculada por Impacto ×
            Urgencia.
          </p>
        </div>
        <Badge variant="exception">Equipo 4 · En construcción</Badge>
      </div>

      {/* Tarjeta informativa de la arquitectura */}
      <Card className="p-8 text-center space-y-4 max-w-2xl mx-auto my-12 border-dashed">
        <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto">
          <AlertTriangle size={24} />
        </div>
        <div className="space-y-1">
          <h4 className="font-semibold text-slate-800 text-lg">Módulo de Incidencias Reservado</h4>
          <p className="text-sm text-slate-500">
            Este espacio está listo para que el <strong>Equipo 4</strong> integre el tablero Kanban
            de incidencias, la matriz de priorización y el detalle de tickets según las
            especificaciones de <code>frontend/DESIGN.md</code>.
          </p>
        </div>
        <div className="pt-2 flex justify-center gap-2">
          <Badge variant="outline" className="text-xs">
            <Clock size={12} className="mr-1" />
            Línea de vida ITIL
          </Badge>
          <Badge variant="outline" className="text-xs">
            <ShieldAlert size={12} className="mr-1" />
            Matriz Impacto × Urgencia
          </Badge>
        </div>
      </Card>
    </div>
  )
}
