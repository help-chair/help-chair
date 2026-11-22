import { Eye, FileText, Globe, Lock, ThumbsUp } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { UMBRAL_MEJORA, codigoError, formatFecha, nombreCategoria, porcentajeUtil } from './data'
import type { Articulo } from './types'

interface ArticleListProps {
  articulos: Articulo[]
  onAbrir: (articuloId: string) => void
}

/** Tarjetas de artículos: título, resumen y señales de utilidad. */
export function ArticleList({ articulos, onAbrir }: ArticleListProps) {
  return (
    <ul className="space-y-3">
      {articulos.map((articulo) => {
        const util = porcentajeUtil(articulo)
        const publico = articulo.visibilidad === 'publico'
        return (
          <li key={articulo.id}>
            <Card className="flex items-start gap-4 p-5 transition-colors hover:border-primary/40">
              <span className="shrink-0 rounded-lg bg-emerald-50 p-2.5 text-emerald-700">
                <FileText size={20} aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-bold text-slate-600">{articulo.id}</span>
                  {articulo.error_conocido_id !== null && (
                    <Badge variant="warning">
                      Solución temporal · {codigoError(articulo.error_conocido_id)}
                    </Badge>
                  )}
                </div>
                <h4 className="mt-1 text-base font-semibold text-slate-800">
                  <button
                    type="button"
                    onClick={() => onAbrir(articulo.id)}
                    className="rounded text-left hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {articulo.titulo}
                  </button>
                </h4>
                <p className="mt-1 max-w-prose text-sm text-slate-600">{articulo.resumen}</p>
                <p className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span className="rounded-md bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
                    {nombreCategoria(articulo.categoria)}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    {publico ? (
                      <Globe size={14} aria-hidden="true" />
                    ) : (
                      <Lock size={14} aria-hidden="true" />
                    )}
                    {publico ? 'Público' : 'Solo agentes'}
                  </span>
                  <span
                    className={cn(
                      'inline-flex items-center gap-1 font-semibold',
                      util < UMBRAL_MEJORA ? 'text-amber-800' : 'text-emerald-700',
                    )}
                  >
                    <ThumbsUp size={14} aria-hidden="true" />
                    {util} % útil
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Eye size={14} aria-hidden="true" />
                    {articulo.consultas} consultas
                  </span>
                  <span>
                    Actualizado el{' '}
                    <time dateTime={articulo.actualizado_en}>
                      {formatFecha(articulo.actualizado_en)}
                    </time>
                  </span>
                </p>
              </div>
            </Card>
          </li>
        )
      })}
    </ul>
  )
}
