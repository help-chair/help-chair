import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ESTADOS } from './data'
import type { EstadoProblema } from './types'

type EstadoPaso = 'hecho' | 'actual' | 'pendiente'

const TEXTO_LECTOR: Record<EstadoPaso, string> = {
  hecho: 'completado',
  actual: 'estado actual',
  pendiente: 'pendiente',
}

/** Ciclo de vida del contrato: Registrado → En análisis → … → Cerrado. */
export function ProblemLifecycle({ estado }: { estado: EstadoProblema }) {
  const indiceActual = ESTADOS.findIndex((opcion) => opcion.value === estado)

  return (
    <ol
      aria-label="Ciclo de vida del problema"
      className="flex flex-col gap-3 sm:flex-row sm:gap-0"
    >
      {ESTADOS.map((paso, indice) => {
        const estadoPaso: EstadoPaso =
          indice < indiceActual || estado === 'cerrado'
            ? 'hecho'
            : indice === indiceActual
              ? 'actual'
              : 'pendiente'

        return (
          <li
            key={paso.value}
            aria-current={estadoPaso === 'actual' ? 'step' : undefined}
            className="relative flex items-center gap-3 sm:flex-1 sm:flex-col sm:gap-2 sm:text-center"
          >
            {indice < ESTADOS.length - 1 && (
              <span
                aria-hidden="true"
                className={cn(
                  'absolute top-4 left-1/2 ml-5 hidden h-0.5 w-[calc(100%-2.5rem)] rounded-full sm:block',
                  indice < indiceActual ? 'bg-itil-success' : 'bg-slate-200',
                )}
              />
            )}
            <span
              aria-hidden="true"
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold',
                estadoPaso === 'hecho' && 'border-itil-success bg-itil-success text-white',
                estadoPaso === 'actual' &&
                  'border-primary bg-white text-primary ring-4 ring-primary/15',
                estadoPaso === 'pendiente' && 'border-slate-200 bg-white text-slate-400',
              )}
            >
              {estadoPaso === 'hecho' ? <Check size={16} /> : indice + 1}
            </span>
            <span
              className={cn(
                'block text-xs font-semibold',
                estadoPaso === 'actual' && 'text-primary',
                estadoPaso === 'hecho' && 'text-slate-800',
                estadoPaso === 'pendiente' && 'text-slate-500',
              )}
            >
              {paso.label}
              <span className="sr-only"> ({TEXTO_LECTOR[estadoPaso]})</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}
