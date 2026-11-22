import { useState } from 'react'
import { SearchX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/form'
import { cn } from '@/lib/utils'
import { ANALISTAS, ESTADOS, ORIGENES, PRIORIDADES, codigoProblema, formatFecha } from './data'
import { EstadoBadge, OrigenEtiqueta, PrioridadBadge } from './ProblemBadges'
import type { EstadoProblema, Origen, Prioridad, Problema, ProblemaIncidente } from './types'

interface ProblemTableProps {
  problemas: Problema[]
  incidentes: ProblemaIncidente[]
  resaltadoId: number | null
  onVerDetalle: (problemaId: number) => void
}

const COLUMNAS = ['ID', 'Problema', 'Prioridad', 'Estado', 'Incidencias', 'Asignado a', 'Acción']

function Iniciales({ nombre }: { nombre: string }) {
  const iniciales = nombre
    .split(' ')
    .map((parte) => parte[0] ?? '')
    .slice(0, 2)
    .join('')
  return (
    <span
      aria-hidden="true"
      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-semibold text-indigo-700"
    >
      {iniciales}
    </span>
  )
}

/** Tabla «Problemas registrados» con los filtros que acepta el contrato: estado, prioridad y origen. */
export function ProblemTable({
  problemas,
  incidentes,
  resaltadoId,
  onVerDetalle,
}: ProblemTableProps) {
  const [estado, setEstado] = useState<EstadoProblema | 'todos'>('todos')
  const [prioridad, setPrioridad] = useState<Prioridad | 'todas'>('todas')
  const [origen, setOrigen] = useState<Origen | 'todos'>('todos')

  const visibles = problemas.filter(
    (problema) =>
      (estado === 'todos' || problema.estado === estado) &&
      (prioridad === 'todas' || problema.prioridad === prioridad) &&
      (origen === 'todos' || problema.origen === origen),
  )

  function quitarFiltros() {
    setEstado('todos')
    setPrioridad('todas')
    setOrigen('todos')
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 space-y-0">
        <div className="space-y-1.5">
          <CardTitle className="text-base">Problemas registrados</CardTitle>
          <CardDescription>
            Causa raíz, prioridad y estado de cada problema según ITIL v4
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Select
            aria-label="Filtrar por estado"
            value={estado}
            className="h-8 w-48 text-xs"
            onChange={(event) => setEstado(event.target.value as EstadoProblema | 'todos')}
          >
            <option value="todos">Estado: todos</option>
            {ESTADOS.map((opcion) => (
              <option key={opcion.value} value={opcion.value}>
                Estado: {opcion.label.toLowerCase()}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Filtrar por prioridad"
            value={prioridad}
            className="h-8 w-40 text-xs"
            onChange={(event) => setPrioridad(event.target.value as Prioridad | 'todas')}
          >
            <option value="todas">Prioridad: todas</option>
            {PRIORIDADES.map((opcion) => (
              <option key={opcion.value} value={opcion.value}>
                Prioridad: {opcion.label.toLowerCase()}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Filtrar por origen"
            value={origen}
            className="h-8 w-48 text-xs"
            onChange={(event) => setOrigen(event.target.value as Origen | 'todos')}
          >
            <option value="todos">Origen: todos</option>
            {ORIGENES.map((opcion) => (
              <option key={opcion.value} value={opcion.value}>
                Origen: {opcion.label.toLowerCase()}
              </option>
            ))}
          </Select>
        </div>
      </CardHeader>

      {visibles.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <SearchX size={40} aria-hidden="true" className="mb-2 text-slate-400" />
          <p className="text-base font-semibold text-slate-800">
            Ningún problema coincide con esos filtros
          </p>
          <p className="mb-4 text-sm text-slate-500">Prueba con otra combinación o quítalos.</p>
          <Button variant="outline" size="sm" onClick={quitarFiltros}>
            Quitar filtros
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[56rem] text-left text-sm">
            <caption className="sr-only">Problemas registrados</caption>
            <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
              <tr>
                {COLUMNAS.map((columna) => (
                  <th key={columna} scope="col" className="whitespace-nowrap px-4 py-3">
                    {columna}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {visibles.map((problema) => {
                const codigo = codigoProblema(problema.id)
                const total = incidentes.filter(
                  (vinculo) => vinculo.problema_id === problema.id,
                ).length
                const analista = ANALISTAS[problema.asignado_a_id]
                return (
                  <tr
                    key={problema.id}
                    className={cn('align-top', problema.id === resaltadoId && 'bg-primary/5')}
                  >
                    <td className="px-4 py-3">
                      <p className="whitespace-nowrap font-mono text-xs font-bold text-slate-900">
                        {codigo}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        <time dateTime={problema.creado_en}>{formatFecha(problema.creado_en)}</time>
                      </p>
                    </td>
                    <td className="min-w-[18rem] px-4 py-3">
                      <p className="font-semibold text-slate-800">{problema.titulo}</p>
                      <p className="mt-1 text-xs text-slate-500">{problema.descripcion}</p>
                      <p className="mt-2">
                        <OrigenEtiqueta origen={problema.origen} />
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <PrioridadBadge prioridad={problema.prioridad} />
                    </td>
                    <td className="px-4 py-3">
                      <EstadoBadge estado={problema.estado} />
                    </td>
                    <td className="px-4 py-3 text-center font-semibold text-slate-800">{total}</td>
                    <td className="px-4 py-3">
                      {analista ? (
                        <span className="flex items-center gap-2 whitespace-nowrap text-slate-700">
                          <Iniciales nombre={analista} />
                          {analista}
                        </span>
                      ) : (
                        <span className="whitespace-nowrap text-slate-500">Sin asignar</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="outline"
                        size="sm"
                        className="whitespace-nowrap"
                        aria-label={`Ver análisis de ${codigo}`}
                        onClick={() => onVerDetalle(problema.id)}
                      >
                        Ver análisis
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}
