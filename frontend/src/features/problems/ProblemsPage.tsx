import { AlertOctagon, HelpCircle, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export function ProblemsPage() {
  return (
    <div className="space-y-6">
      {/* Banner de la Práctica */}
      <div className="bg-white border border-border p-6 rounded-xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
              <ShieldAlert size={20} />
            </span>
            <h3 className="text-xl font-bold text-slate-900">
              Gestión de Problemas (Problem Management)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1 max-w-3xl">
            Práctica ITIL v4: Reducir la probabilidad y el impacto de los incidentes identificando
            sus causas reales y potenciales, y gestionando soluciones temporales (workarounds) y
            errores conocidos (KEDB).
          </p>
        </div>
        <Badge variant="warning">Equipo 5 · En construcción</Badge>
      </div>

      {/* Tarjeta informativa de la arquitectura */}
      <Card className="p-8 text-center space-y-4 max-w-2xl mx-auto my-12 border-dashed">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
          <AlertOctagon size={24} />
        </div>
        <div className="space-y-1">
          <h4 className="font-semibold text-slate-800 text-lg">Módulo de Problemas Reservado</h4>
          <p className="text-sm text-slate-500">
            Este espacio está preparado para que el <strong>Equipo 5</strong> implemente el registro
            de Causa Raíz (RCA) y la base de datos de errores conocidos (KEDB) según{' '}
            <code>frontend/DESIGN.md</code>.
          </p>
        </div>
        <div className="pt-2 flex justify-center gap-2">
          <Badge variant="outline" className="text-xs">
            <HelpCircle size={12} className="mr-1" />
            Análisis de Causa Raíz
          </Badge>
          <Badge variant="outline" className="text-xs">
            KEDB (Known Errors)
          </Badge>
        </div>
      </Card>
    </div>
  )
}
