import { BookOpen, FileText, Search, ThumbsUp } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export function KnowledgePage() {
  return (
    <div className="space-y-6">
      {/* Banner de la Práctica */}
      <div className="bg-white border border-border p-6 rounded-xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <BookOpen size={20} />
            </span>
            <h3 className="text-xl font-bold text-slate-900">
              Base de Conocimiento (Knowledge Management)
            </h3>
          </div>
          <p className="text-sm text-slate-500 mt-1 max-w-3xl">
            Práctica ITIL v4: Mantener y mejorar el uso efectivo, eficiente y conveniente de la
            información y el conocimiento a través de la organización.
          </p>
        </div>
        <Badge variant="success">Equipo 5 · En construcción</Badge>
      </div>

      {/* Tarjeta informativa de la arquitectura */}
      <Card className="p-8 text-center space-y-4 max-w-2xl mx-auto my-12 border-dashed">
        <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
          <FileText size={24} />
        </div>
        <div className="space-y-1">
          <h4 className="font-semibold text-slate-800 text-lg">
            Base de Conocimiento (KB) Reservada
          </h4>
          <p className="text-sm text-slate-500">
            Este espacio está preparado para que el <strong>Equipo 5</strong> implemente el motor de
            búsqueda de artículos, autoservicio para usuarios y sugerencias automáticas de solución.
          </p>
        </div>
        <div className="pt-2 flex justify-center gap-2">
          <Badge variant="outline" className="text-xs">
            <Search size={12} className="mr-1" />
            Buscador de Artículos
          </Badge>
          <Badge variant="outline" className="text-xs">
            <ThumbsUp size={12} className="mr-1" />
            Feedback de Utilidad
          </Badge>
        </div>
      </Card>
    </div>
  )
}
