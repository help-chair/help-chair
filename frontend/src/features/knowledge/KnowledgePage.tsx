import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { BookOpen, Search, SearchX, ThumbsDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/form'
import { cn } from '@/lib/utils'
import { ArticleList } from './ArticleList'
import { ArticleView } from './ArticleView'
import { CATEGORIAS, UMBRAL_MEJORA, buscarArticulos, porcentajeUtil } from './data'
import type { Articulo, Categoria } from './types'
import { useArticulos } from './useArticulos'

interface KnowledgePageProps {
  /** Para pruebas: reemplaza la carga de artículos de ejemplo. */
  cargarArticulos?: () => Promise<Articulo[]>
}

/**
 * Módulo de Base de Conocimiento (Equipo 5 · Knowledge Management), según el diseño de
 * frontend/docs/knowledge/. Trabaja con artículos de ejemplo en memoria hasta que
 * services/knowledge publique su API (contracts/knowledge/openapi.yaml).
 */
export function KnowledgePage({ cargarArticulos }: KnowledgePageProps) {
  const modulo = useArticulos(cargarArticulos)
  const buscadorId = useId()
  const [texto, setTexto] = useState('')
  const [consulta, setConsulta] = useState('')
  const [categoria, setCategoria] = useState<Categoria | 'todas'>('todas')
  const [abiertoId, setAbiertoId] = useState<string | null>(null)
  const inicioRef = useRef<HTMLDivElement>(null)

  const abierto = modulo.articulos.find((articulo) => articulo.id === abiertoId)
  const resultados = buscarArticulos(modulo.articulos, consulta, categoria)
  const masUtiles = [...modulo.articulos]
    .sort((a, b) => porcentajeUtil(b) - porcentajeUtil(a))
    .slice(0, 3)
  const porMejorar = modulo.articulos.filter((articulo) => porcentajeUtil(articulo) < UMBRAL_MEJORA)

  function buscar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setConsulta(texto.trim())
  }

  function limpiar() {
    setTexto('')
    setConsulta('')
    setCategoria('todas')
  }

  function abrir(articuloId: string) {
    setAbiertoId(articuloId)
    modulo.registrarConsulta(articuloId)
  }

  // Al abrir o cerrar un artículo, vuelve arriba para que se vea su inicio.
  useEffect(() => {
    inicioRef.current?.scrollIntoView?.({ block: 'start' })
  }, [abiertoId])

  if (abierto) {
    return (
      <div ref={inicioRef} className="scroll-mt-16">
        <ArticleView
          articulo={abierto}
          relacionados={modulo.articulos.filter(
            (articulo) => articulo.categoria === abierto.categoria && articulo.id !== abierto.id,
          )}
          onVolver={() => setAbiertoId(null)}
          onAbrir={abrir}
          onValorar={modulo.valorar}
        />
      </div>
    )
  }

  return (
    // `relative` mantiene los textos sr-only (posición absoluta) dentro del área con scroll.
    <div ref={inicioRef} className="relative scroll-mt-16 space-y-6">
      <section
        aria-labelledby="kb-titulo"
        className="space-y-5 rounded-xl bg-gradient-to-r from-indigo-700 via-indigo-800 to-slate-900 p-6 text-white shadow-sm"
      >
        <div className="max-w-3xl space-y-1">
          <h3 id="kb-titulo" className="text-xl font-bold">
            Base de Conocimiento
          </h3>
          <p className="text-sm text-indigo-100">
            Soluciones paso a paso a los problemas más comunes. Si un artículo no te sirve, avísanos
            y lo mejoramos.
          </p>
        </div>
        <form role="search" onSubmit={buscar} className="flex flex-col gap-2 sm:flex-row">
          <label htmlFor={buscadorId} className="sr-only">
            Buscar en la Base de Conocimiento
          </label>
          <div className="relative flex-1">
            <Search
              size={16}
              aria-hidden="true"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <Input
              id={buscadorId}
              type="search"
              value={texto}
              placeholder="Describe tu problema, por ejemplo: no tengo wifi en el edificio B"
              className="h-11 pl-9"
              onChange={(event) => {
                setTexto(event.target.value)
                if (!event.target.value) setConsulta('')
              }}
            />
          </div>
          <Button
            type="submit"
            size="lg"
            className="h-11 bg-white text-indigo-800 hover:bg-indigo-50"
          >
            Buscar solución
          </Button>
        </form>
        <div
          className="flex flex-wrap items-center gap-2"
          role="group"
          aria-label="Filtrar por etiqueta"
        >
          {[{ value: 'todas' as const, label: 'Todas' }, ...CATEGORIAS].map((opcion) => {
            const activa = categoria === opcion.value
            const total =
              opcion.value === 'todas'
                ? modulo.articulos.length
                : modulo.articulos.filter((articulo) => articulo.categoria === opcion.value).length
            return (
              <button
                key={opcion.value}
                type="button"
                aria-pressed={activa}
                onClick={() => setCategoria(opcion.value)}
                className={cn(
                  'rounded-full border px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white',
                  activa
                    ? 'border-white bg-white text-indigo-800'
                    : 'border-white/30 bg-white/10 text-white hover:bg-white/20',
                )}
              >
                {opcion.label} · {total}
              </button>
            )
          })}
        </div>
      </section>

      {modulo.carga === 'cargando' && (
        <div aria-busy="true" className="space-y-3">
          <p className="sr-only">Cargando artículos…</p>
          {[0, 1, 2].map((indice) => (
            <Card key={indice} className="h-32 animate-pulse bg-slate-50" />
          ))}
        </div>
      )}

      {modulo.carga === 'error' && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <p className="font-medium">No se pudieron cargar los artículos.</p>
          <p className="mt-1 text-xs text-red-700">
            Verifica tu conexión con la Base de Conocimiento e inténtalo de nuevo.
          </p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => modulo.recargar()}>
            Reintentar
          </Button>
        </div>
      )}

      {modulo.carga === 'lista' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <section aria-labelledby="kb-resultados" className="space-y-3 lg:col-span-2">
            <h4 id="kb-resultados" className="text-base font-semibold text-slate-800">
              {consulta
                ? `${resultados.length} ${resultados.length === 1 ? 'resultado' : 'resultados'} para «${consulta}»`
                : 'Artículos recientes'}
            </h4>
            {resultados.length === 0 ? (
              <Card className="flex flex-col items-center justify-center p-8 text-center">
                <SearchX size={40} aria-hidden="true" className="mb-2 text-slate-400" />
                <p className="text-base font-semibold text-slate-800">
                  {consulta
                    ? `No encontramos artículos para «${consulta}»`
                    : 'Aún no hay artículos en esta etiqueta'}
                </p>
                <p className="mb-4 text-sm text-slate-500">
                  Prueba con otras palabras o revisa todas las etiquetas.
                </p>
                <Button variant="outline" size="sm" onClick={limpiar}>
                  Limpiar búsqueda
                </Button>
              </Card>
            ) : (
              <ArticleList articulos={resultados} onAbrir={abrir} />
            )}
          </section>

          <aside className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Más útiles</CardTitle>
                <CardDescription>Los que más personas marcaron como útiles</CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3">
                  {masUtiles.map((articulo, indice) => (
                    <li key={articulo.id} className="flex items-start gap-3">
                      <span
                        aria-hidden="true"
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-bold text-indigo-700"
                      >
                        {indice + 1}
                      </span>
                      <div className="min-w-0">
                        <button
                          type="button"
                          onClick={() => abrir(articulo.id)}
                          className="rounded text-left text-sm font-semibold text-slate-800 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                          {articulo.titulo}
                        </button>
                        <p className="text-xs text-emerald-700">
                          {porcentajeUtil(articulo)} % útil
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>

            <Card className="border-amber-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ThumbsDown size={16} aria-hidden="true" className="text-amber-800" />
                  Necesitan mejora
                </CardTitle>
                <CardDescription>
                  Les sirvieron a menos del {UMBRAL_MEJORA} % de quienes los leyeron
                </CardDescription>
              </CardHeader>
              <CardContent>
                {porMejorar.length === 0 ? (
                  <p className="flex items-center gap-2 text-sm text-slate-500">
                    <BookOpen size={16} aria-hidden="true" />
                    Todos los artículos van bien.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {porMejorar.map((articulo) => (
                      <li
                        key={articulo.id}
                        className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm"
                      >
                        <button
                          type="button"
                          onClick={() => abrir(articulo.id)}
                          className="rounded text-left font-semibold text-amber-900 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                          {articulo.id} · {articulo.titulo}
                        </button>
                        <p className="mt-1 text-xs text-amber-800">
                          {articulo.votos_no_utiles} personas dijeron que no les sirvió
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </aside>
        </div>
      )}
    </div>
  )
}
