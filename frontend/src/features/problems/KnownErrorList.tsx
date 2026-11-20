import { BookOpen, CheckCircle2, Wrench } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { codigoError, codigoProblema } from './data'
import type { ErrorConocido } from './types'

interface KnownErrorListProps {
  errores: ErrorConocido[]
  onVerProblema: (problemaId: number) => void
}

/** Base de errores conocidos (KEDB): la solución temporal que aplica el Service Desk. */
export function KnownErrorList({ errores, onVerProblema }: KnownErrorListProps) {
  const activos = errores.filter((error) => error.activo).length
  const ordenados = [...errores].sort((a, b) => Number(b.activo) - Number(a.activo))

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="text-base">Base de errores conocidos (KEDB)</CardTitle>
          <CardDescription>
            Soluciones temporales que el Service Desk puede aplicar mientras se corrige la causa
            raíz
          </CardDescription>
        </div>
        <Badge variant="warning">
          {activos} {activos === 1 ? 'activo' : 'activos'} · {errores.length - activos}{' '}
          {errores.length - activos === 1 ? 'retirado' : 'retirados'}
        </Badge>
      </CardHeader>

      {errores.length === 0 ? (
        <p className="p-6 text-sm text-slate-500">
          Aún no hay errores conocidos. Se publican desde el detalle de un problema, después de
          identificar su causa raíz.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-4 p-6 md:grid-cols-3">
          {ordenados.map((error) => (
            <li
              key={error.id}
              className={cn(
                'flex flex-col gap-3 rounded-xl border p-4',
                error.activo ? 'border-border' : 'border-dashed border-slate-300 bg-slate-50',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-bold text-slate-900">
                  {codigoError(error.id)}
                </span>
                <Badge variant={error.activo ? 'success' : 'outline'}>
                  {error.activo ? 'Activo' : 'Retirado'}
                </Badge>
              </div>
              <h4 className="text-sm font-semibold text-slate-800">{error.titulo}</h4>
              <p className="text-sm text-slate-600">
                <strong className="font-medium text-slate-700">Causa raíz:</strong>{' '}
                {error.causa_raiz}
              </p>
              <div
                className={cn(
                  'rounded-lg border p-3',
                  error.activo ? 'border-amber-200 bg-amber-50' : 'border-border bg-white',
                )}
              >
                <p
                  className={cn(
                    'flex items-center gap-1.5 text-xs font-semibold',
                    error.activo ? 'text-amber-800' : 'text-slate-600',
                  )}
                >
                  {error.activo ? (
                    <Wrench size={14} aria-hidden="true" />
                  ) : (
                    <CheckCircle2 size={14} aria-hidden="true" />
                  )}
                  {error.activo ? 'Solución temporal' : 'Ya no se necesita'}
                </p>
                <p className="mt-1 text-sm text-slate-700">{error.workaround}</p>
              </div>
              <div className="mt-auto flex flex-wrap items-center gap-3 text-xs">
                <Button
                  variant="ghost"
                  size="sm"
                  className="-ml-3 text-primary"
                  onClick={() => onVerProblema(error.problema_id)}
                >
                  Ver {codigoProblema(error.problema_id)}
                </Button>
                {error.articulo_kb_id && (
                  <span className="inline-flex items-center gap-1 font-medium text-emerald-700">
                    <BookOpen size={14} aria-hidden="true" />
                    Artículo {error.articulo_kb_id}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
