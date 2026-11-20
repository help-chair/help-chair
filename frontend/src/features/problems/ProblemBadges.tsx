import { AlertTriangle, Repeat, User } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { ESTADOS, PRIORIDADES, TONO_PUNTO, buscarOpcion } from './data'
import type { EstadoProblema, Origen, Prioridad } from './types'

// Etiquetas reutilizadas por la tabla y el detalle. El color nunca va solo: siempre lleva texto.

export function EstadoBadge({ estado }: { estado: EstadoProblema }) {
  const opcion = buscarOpcion(ESTADOS, estado)
  return (
    <Badge variant={opcion.variant} className="whitespace-nowrap">
      <span
        className={cn('h-1.5 w-1.5 rounded-full', TONO_PUNTO[opcion.variant])}
        aria-hidden="true"
      />
      {opcion.label}
    </Badge>
  )
}

export function PrioridadBadge({ prioridad }: { prioridad: Prioridad }) {
  const opcion = buscarOpcion(PRIORIDADES, prioridad)
  return (
    <Badge variant={opcion.variant} className="whitespace-nowrap">
      {prioridad === 'critica' && <AlertTriangle size={12} aria-hidden="true" />}
      {opcion.label}
    </Badge>
  )
}

export function OrigenEtiqueta({ origen }: { origen: Origen }) {
  const patron = origen === 'patron'
  const Icon = patron ? Repeat : User
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium',
        patron ? 'text-blue-700' : 'text-slate-600',
      )}
    >
      <Icon size={14} aria-hidden="true" />
      {patron ? 'Patrón detectado' : 'Manual'}
    </span>
  )
}
