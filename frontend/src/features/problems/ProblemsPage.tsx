import { useEffect, useRef, useState } from 'react'
import { Info, Plus, ShieldAlert, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { AVANCES, codigoError, codigoProblema, siguienteEstado } from './data'
import { KnownErrorList } from './KnownErrorList'
import { ProblemDetail } from './ProblemDetail'
import { ProblemMetrics } from './ProblemMetrics'
import {
  CausaRaizModal,
  ErrorConocidoModal,
  NuevoProblemaModal,
  VincularIncidenciaModal,
} from './ProblemModals'
import { ProblemTable } from './ProblemTable'
import type { DatosProblemas, ErrorConocidoCrear, Problema, ProblemaCrear } from './types'
import { useProblemas } from './useProblemas'

type Vista = { nombre: 'lista' } | { nombre: 'detalle'; problemaId: number }

type Dialogo =
  { tipo: 'nuevo' } | { tipo: 'vincular' | 'causa' | 'error'; problema: Problema } | null

interface ProblemsPageProps {
  /** Para pruebas: reemplaza la carga desde services/problems. */
  cargarDatos?: () => Promise<DatosProblemas>
}

/**
 * Módulo de Problemas (Equipo 5 · Problem Management), según el diseño de
 * frontend/docs/problems/. Lee y modifica los datos en services/problems
 * (contracts/problems/openapi.yaml).
 */
export function ProblemsPage({ cargarDatos }: ProblemsPageProps) {
  const modulo = useProblemas(cargarDatos)
  const [vista, setVista] = useState<Vista>({ nombre: 'lista' })
  const [dialogo, setDialogo] = useState<Dialogo>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [resaltadoId, setResaltadoId] = useState<number | null>(null)
  const inicioRef = useRef<HTMLDivElement>(null)

  // Al cambiar entre la lista y el detalle, vuelve arriba para que se vea el inicio y el aviso.
  useEffect(() => {
    inicioRef.current?.scrollIntoView?.({ block: 'start' })
  }, [vista])

  const seleccionado =
    vista.nombre === 'detalle'
      ? modulo.problemas.find((problema) => problema.id === vista.problemaId)
      : undefined

  function verDetalle(problemaId: number) {
    setVista({ nombre: 'detalle', problemaId })
    setAviso(null)
  }

  /** Registra el problema; devuelve el error para el modal o `null` si salió bien. */
  async function registrar(entrada: ProblemaCrear): Promise<string | null> {
    const resultado = await modulo.registrar(entrada)
    if (!resultado.ok) return resultado.detalle
    setDialogo(null)
    setResaltadoId(resultado.valor.id)
    setVista({ nombre: 'lista' })
    setAviso(
      `Problema ${codigoProblema(resultado.valor.id)} registrado. Aparece al inicio de la tabla.`,
    )
    return null
  }

  /** Avanza al siguiente estado; los que piden datos abren su formulario primero. */
  async function avanzar(problema: Problema) {
    const destino = siguienteEstado(problema.estado)
    if (!destino) return
    if (destino === 'causa_identificada') return setDialogo({ tipo: 'causa', problema })
    if (destino === 'error_conocido') return setDialogo({ tipo: 'error', problema })
    const resultado = await modulo.cambiarEstado(problema.id, { estado: destino })
    setAviso(
      resultado.ok
        ? AVANCES[destino as keyof typeof AVANCES].aviso(codigoProblema(problema.id))
        : resultado.detalle,
    )
  }

  async function registrarCausa(problema: Problema, causaRaiz: string): Promise<string | null> {
    const resultado = await modulo.cambiarEstado(problema.id, {
      estado: 'causa_identificada',
      causa_raiz: causaRaiz,
    })
    if (!resultado.ok) return resultado.detalle
    setDialogo(null)
    setAviso(AVANCES.causa_identificada.aviso(codigoProblema(problema.id)))
    return null
  }

  /** Publica el error conocido y luego pasa el problema a `error_conocido`. */
  async function publicarError(
    problema: Problema,
    entrada: ErrorConocidoCrear,
  ): Promise<string | null> {
    const error = await modulo.crearErrorConocido(entrada)
    if (!error.ok) return error.detalle
    const resultado = await modulo.cambiarEstado(problema.id, { estado: 'error_conocido' })
    setDialogo(null)
    setAviso(
      resultado.ok
        ? `Error conocido ${codigoError(error.valor.id)} publicado para ${codigoProblema(problema.id)}.`
        : `Error conocido ${codigoError(error.valor.id)} publicado, pero ${codigoProblema(problema.id)} no cambió de estado: ${resultado.detalle}`,
    )
    return null
  }

  async function vincular(problema: Problema, incidenteId: string): Promise<string | null> {
    const resultado = await modulo.vincular(problema.id, incidenteId)
    if (!resultado.ok) return resultado.detalle
    setDialogo(null)
    setAviso(
      `Incidencia ${resultado.valor.incidente_id} vinculada a ${codigoProblema(problema.id)}.`,
    )
    return null
  }

  async function desvincular(problema: Problema, incidenteId: string) {
    const resultado = await modulo.desvincular(problema.id, incidenteId)
    setAviso(
      resultado.ok
        ? `Incidencia ${incidenteId} desvinculada de ${codigoProblema(problema.id)}.`
        : resultado.detalle,
    )
  }

  const problemaDialogo = (tipo: 'vincular' | 'causa' | 'error') =>
    dialogo && dialogo.tipo === tipo ? dialogo.problema : null

  return (
    // `relative` mantiene los textos sr-only (posición absoluta) dentro del área con scroll.
    <div ref={inicioRef} className="relative scroll-mt-16 space-y-6">
      {!seleccionado && (
        <section
          aria-labelledby="problemas-titulo"
          className="flex flex-col gap-4 rounded-xl bg-gradient-to-r from-indigo-700 via-indigo-800 to-slate-900 p-6 text-white shadow-sm md:flex-row md:items-center md:justify-between"
        >
          <div className="max-w-3xl space-y-1">
            <h3 id="problemas-titulo" className="text-xl font-bold">
              Gestión de Problemas
            </h3>
            <p className="text-sm text-indigo-100">
              Encuentra la causa raíz de las incidencias que se repiten y documenta soluciones
              temporales para que el Service Desk resuelva más rápido mientras se corrige el fondo
              del problema.
            </p>
          </div>
          <Button
            variant="outline"
            className="shrink-0 border-white/30 bg-white/10 text-white hover:bg-white/20"
            disabled={modulo.carga !== 'lista'}
            onClick={() => setDialogo({ tipo: 'nuevo' })}
          >
            <Plus size={16} aria-hidden="true" />
            Registrar problema
          </Button>
        </section>
      )}

      {/* Región viva siempre presente para que los lectores de pantalla anuncien cada acción. */}
      <div role="status" className={cn(!aviso && 'sr-only')}>
        {aviso && (
          <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-700">
            <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
            <p className="flex-1">{aviso}</p>
            <button
              type="button"
              aria-label="Cerrar aviso"
              onClick={() => setAviso(null)}
              className="rounded p-0.5 hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>

      {modulo.carga === 'cargando' && <Cargando />}

      {modulo.carga === 'error' && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <p className="font-medium">No se pudieron cargar los problemas.</p>
          <p className="mt-1 text-xs text-red-700">{modulo.errorCarga}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => modulo.recargar()}>
            Reintentar
          </Button>
        </div>
      )}

      {modulo.carga === 'lista' &&
        (seleccionado ? (
          <ProblemDetail
            problema={seleccionado}
            incidentes={modulo.incidentes.filter(
              (vinculo) => vinculo.problema_id === seleccionado.id,
            )}
            errorConocido={
              modulo.errores.find(
                (error) => error.problema_id === seleccionado.id && error.activo,
              ) ?? modulo.errores.find((error) => error.problema_id === seleccionado.id)
            }
            analisis={modulo.analisis[seleccionado.id]}
            onVolver={() => setVista({ nombre: 'lista' })}
            onAvanzar={() => void avanzar(seleccionado)}
            onVincular={() => setDialogo({ tipo: 'vincular', problema: seleccionado })}
            onDesvincular={(incidenteId) => void desvincular(seleccionado, incidenteId)}
          />
        ) : modulo.problemas.length === 0 ? (
          <Card className="flex flex-col items-center justify-center p-8 text-center">
            <ShieldAlert size={40} aria-hidden="true" className="mb-2 text-slate-400" />
            <h4 className="text-base font-semibold text-slate-800">
              Aún no hay problemas registrados
            </h4>
            <p className="mb-4 text-sm text-slate-500">
              ¿Una incidencia se repite? Registra un problema para encontrar su causa raíz.
            </p>
            <Button onClick={() => setDialogo({ tipo: 'nuevo' })}>Registrar problema</Button>
          </Card>
        ) : (
          <>
            <ProblemMetrics
              problemas={modulo.problemas}
              incidentes={modulo.incidentes}
              errores={modulo.errores}
            />
            <ProblemTable
              problemas={modulo.problemas}
              incidentes={modulo.incidentes}
              resaltadoId={resaltadoId}
              onVerDetalle={verDetalle}
            />
            <KnownErrorList errores={modulo.errores} onVerProblema={verDetalle} />
          </>
        ))}

      <NuevoProblemaModal
        open={dialogo?.tipo === 'nuevo'}
        onClose={() => setDialogo(null)}
        onRegistrar={registrar}
      />
      <VincularIncidenciaModal
        problema={problemaDialogo('vincular')}
        onClose={() => setDialogo(null)}
        onVincular={async (incidenteId) => {
          const problema = problemaDialogo('vincular')
          return problema ? vincular(problema, incidenteId) : null
        }}
      />
      <CausaRaizModal
        problema={problemaDialogo('causa')}
        onClose={() => setDialogo(null)}
        onRegistrar={async (causaRaiz) => {
          const problema = problemaDialogo('causa')
          return problema ? registrarCausa(problema, causaRaiz) : null
        }}
      />
      <ErrorConocidoModal
        problema={problemaDialogo('error')}
        onClose={() => setDialogo(null)}
        onPublicar={async (entrada) => {
          const problema = problemaDialogo('error')
          return problema ? publicarError(problema, entrada) : null
        }}
      />
    </div>
  )
}

/** Esqueleto mientras llega la respuesta del servicio. */
function Cargando() {
  return (
    <div aria-busy="true" className="space-y-6">
      <p className="sr-only">Cargando problemas…</p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {[0, 1, 2, 3].map((indice) => (
          <Card key={indice} className="h-28 animate-pulse bg-slate-50" />
        ))}
      </div>
      <Card className="space-y-3 p-6">
        {[0, 1, 2, 3, 4].map((indice) => (
          <div key={indice} className="h-10 animate-pulse rounded-lg bg-slate-100" />
        ))}
      </Card>
    </div>
  )
}
