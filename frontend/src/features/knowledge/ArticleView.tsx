import { useId, useState } from 'react'
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  Globe,
  Lightbulb,
  Lock,
  ThumbsDown,
  ThumbsUp,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, Textarea } from '@/components/ui/form'
import { codigoError, formatFecha, nombreCategoria } from './data'
import type { Articulo, Valoracion } from './types'

interface ArticleViewProps {
  articulo: Articulo
  relacionados: Articulo[]
  onVolver: () => void
  onAbrir: (articuloId: string) => void
  onValorar: (valoracion: Valoracion) => void
}

/** Lector de un artículo con la pregunta «¿Te resultó útil?». */
export function ArticleView({
  articulo,
  relacionados,
  onVolver,
  onAbrir,
  onValorar,
}: ArticleViewProps) {
  const publico = articulo.visibilidad === 'publico'
  const base = `kb-${articulo.id.toLowerCase()}`

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" className="-ml-3 text-primary" onClick={onVolver}>
        <ArrowLeft size={16} aria-hidden="true" />
        Volver a la Base de Conocimiento
      </Button>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-6 sm:p-8">
            <article className="max-w-prose space-y-6">
              <header className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>{nombreCategoria(articulo.categoria)}</Badge>
                  <Badge variant={publico ? 'success' : 'default'}>
                    {publico ? (
                      <Globe size={12} aria-hidden="true" />
                    ) : (
                      <Lock size={12} aria-hidden="true" />
                    )}
                    {publico ? 'Público' : 'Solo agentes'}
                  </Badge>
                  {articulo.error_conocido_id !== null && (
                    <Badge variant="warning">Solución temporal</Badge>
                  )}
                </div>
                <h3 className="text-2xl font-bold text-slate-900">{articulo.titulo}</h3>
                <p className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
                  <span>Por {articulo.autor}</span>
                  <span>
                    Actualizado el{' '}
                    <time dateTime={articulo.actualizado_en}>
                      {formatFecha(articulo.actualizado_en)}
                    </time>
                  </span>
                  <span>{articulo.consultas} consultas</span>
                  <span>{articulo.id}</span>
                </p>
              </header>

              {articulo.error_conocido_id !== null && (
                <p className="flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                  <Lightbulb size={20} aria-hidden="true" className="shrink-0" />
                  <span>
                    Esta es la solución temporal del error conocido{' '}
                    <strong>{codigoError(articulo.error_conocido_id)}</strong>. Dejará de ser
                    necesaria cuando se corrija la causa raíz.
                  </span>
                </p>
              )}

              <section aria-labelledby={`${base}-cuando`} className="space-y-2">
                <h4 id={`${base}-cuando`} className="text-base font-semibold text-slate-800">
                  ¿Cuándo usar este artículo?
                </h4>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {articulo.sintomas.map((sintoma) => (
                    <li key={sintoma}>{sintoma}</li>
                  ))}
                </ul>
              </section>

              <section aria-labelledby={`${base}-pasos`} className="space-y-3">
                <h4 id={`${base}-pasos`} className="text-base font-semibold text-slate-800">
                  Pasos
                </h4>
                <ol className="space-y-3">
                  {articulo.pasos.map((paso, indice) => (
                    <li key={paso} className="flex gap-3 text-sm text-slate-700">
                      <span
                        aria-hidden="true"
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-white"
                      >
                        {indice + 1}
                      </span>
                      <span className="pt-0.5">{paso}</span>
                    </li>
                  ))}
                </ol>
              </section>

              <section aria-labelledby={`${base}-sigue`} className="space-y-2">
                <h4 id={`${base}-sigue`} className="text-base font-semibold text-slate-800">
                  ¿Sigue sin funcionar?
                </h4>
                <p className="text-sm text-slate-700">{articulo.si_no_funciona}</p>
              </section>
            </article>
          </Card>

          <Valorar key={articulo.id} articulo={articulo} onValorar={onValorar} />
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">En este artículo</CardTitle>
            </CardHeader>
            <CardContent>
              <nav aria-label="Secciones del artículo">
                <ul className="space-y-1 text-sm">
                  {[
                    ['cuando', '¿Cuándo usar este artículo?'],
                    ['pasos', 'Pasos'],
                    ['sigue', '¿Sigue sin funcionar?'],
                  ].map(([id, texto]) => (
                    <li key={id}>
                      <a
                        href={`#${base}-${id}`}
                        className="block rounded-lg px-2 py-1.5 text-slate-700 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        {texto}
                      </a>
                    </li>
                  ))}
                </ul>
              </nav>
            </CardContent>
          </Card>

          {relacionados.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Artículos relacionados</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {relacionados.map((relacionado) => (
                    <li key={relacionado.id} className="flex items-start gap-2">
                      <FileText
                        size={16}
                        aria-hidden="true"
                        className="mt-0.5 shrink-0 text-emerald-700"
                      />
                      <button
                        type="button"
                        onClick={() => onAbrir(relacionado.id)}
                        className="rounded text-left text-sm font-medium text-slate-700 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        {relacionado.titulo}
                      </button>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

/** «¿Te resultó útil?»: si no sirvió, pide qué le faltó (opcional) antes de registrar la respuesta. */
function Valorar({
  articulo,
  onValorar,
}: {
  articulo: Articulo
  onValorar: (v: Valoracion) => void
}) {
  const comentarioId = useId()
  const [paso, setPaso] = useState<'pregunta' | 'comentario' | 'gracias'>('pregunta')
  const [comentario, setComentario] = useState('')
  const total = articulo.votos_utiles + articulo.votos_no_utiles

  function responder(util: boolean, texto = '') {
    onValorar({ articulo_id: articulo.id, util, comentario: texto.trim() })
    setPaso('gracias')
  }

  return (
    <Card className="border-indigo-200 p-6">
      <div role="status">
        {paso === 'gracias' && (
          <p className="flex items-center gap-2 text-sm font-medium text-emerald-700">
            <CheckCircle2 size={20} aria-hidden="true" />
            Gracias, registramos tu respuesta. Nos ayuda a mejorar la Base de Conocimiento.
          </p>
        )}
      </div>

      {paso === 'pregunta' && (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h4 className="text-base font-semibold text-slate-800">
              ¿Te resultó útil este artículo?
            </h4>
            <p className="mt-1 text-xs text-slate-500">
              {articulo.votos_utiles} de {total} personas dijeron que sí.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              className="border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
              onClick={() => responder(true)}
            >
              <ThumbsUp size={16} aria-hidden="true" />
              Sí, me sirvió
            </Button>
            <Button variant="outline" onClick={() => setPaso('comentario')}>
              <ThumbsDown size={16} aria-hidden="true" />
              No me sirvió
            </Button>
          </div>
        </div>
      )}

      {paso === 'comentario' && (
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault()
            responder(false, comentario)
          }}
        >
          <Field
            label="¿Qué le faltó al artículo?"
            htmlFor={comentarioId}
            hint="Opcional. Por ejemplo: un paso que no funcionó o algo que no se entiende."
          >
            <Textarea
              id={comentarioId}
              value={comentario}
              rows={3}
              aria-describedby={`${comentarioId}-description`}
              onChange={(event) => setComentario(event.target.value)}
            />
          </Field>
          <div className="flex flex-wrap gap-2">
            <Button type="submit">Enviar respuesta</Button>
            <Button type="button" variant="ghost" onClick={() => setPaso('pregunta')}>
              Cancelar
            </Button>
          </div>
        </form>
      )}
    </Card>
  )
}
