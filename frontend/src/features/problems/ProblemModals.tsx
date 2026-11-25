import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link2, ShieldAlert, Target, Wrench } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Field, Input, Select, Textarea } from '@/components/ui/form'
import { Modal } from '@/components/ui/modal'
import { ANALISTAS, PRIORIDADES, codigoProblema } from './data'
import type { ErrorConocidoCrear, Prioridad, Problema, ProblemaCrear } from './types'

// Los cuatro formularios del módulo. Cada uno vive dentro de <Modal>, así que se reinicia
// solo cada vez que se abre (al cerrarse, el Modal desmonta su contenido).
// Cada acción devuelve una promesa con el mensaje de error del servicio o `null` si salió bien:
// si falla, el modal sigue abierto con lo capturado y explica el motivo.

type Errores = Record<string, string | undefined>

/** Respuesta de la acción: el mensaje de error o `null` si salió bien. */
type Envio = Promise<string | null>

/** Estado del envío al servicio: desactiva el botón y guarda el error que devolvió. */
function useEnvio() {
  const [enviando, setEnviando] = useState(false)
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null)
  async function enviarAlServicio(accion: () => Envio) {
    if (enviando) return
    setEnviando(true)
    setErrorEnvio(null)
    const error = await accion()
    // Si salió bien, el modal se cierra y este formulario se desmonta.
    if (error) {
      setErrorEnvio(error)
      setEnviando(false)
    }
  }
  return { enviando, errorEnvio, enviarAlServicio }
}

const descrito = (id: string, mensaje?: string) => (mensaje ? `${id}-description` : undefined)

/** Pie común: «Cancelar» y el botón con la acción exacta. */
function Acciones({
  onCancelar,
  accion,
  enviando = false,
  errorEnvio = null,
}: {
  onCancelar: () => void
  accion: string
  enviando?: boolean
  errorEnvio?: string | null
}) {
  return (
    <>
      {errorEnvio && (
        <p
          role="alert"
          className="mx-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {errorEnvio}
        </p>
      )}
      <div className="flex justify-end gap-2 border-t border-border/50 p-5">
        <Button type="button" variant="outline" onClick={onCancelar}>
          Cancelar
        </Button>
        <Button type="submit" disabled={enviando}>
          {enviando ? 'Guardando…' : accion}
        </Button>
      </div>
    </>
  )
}

/** Formulario con validación: tras un envío con errores, lleva el foco al primer campo inválido. */
function Formulario({
  errores,
  intentos,
  onSubmit,
  children,
}: {
  errores: Errores
  intentos: number
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  children: ReactNode
}) {
  const ref = useRef<HTMLFormElement>(null)
  useEffect(() => {
    if (intentos > 0) ref.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
  }, [intentos, errores])
  return (
    <form ref={ref} noValidate onSubmit={onSubmit} className="flex min-h-0 flex-1 flex-col">
      {children}
    </form>
  )
}

// ---------------------------------------------------------------------------------------------

interface NuevoProblemaModalProps {
  open: boolean
  onClose: () => void
  onRegistrar: (entrada: ProblemaCrear) => Envio
}

export function NuevoProblemaModal({ open, onClose, onRegistrar }: NuevoProblemaModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Registrar problema"
      description="Abre un problema para investigar la causa de fondo de una o varias incidencias"
      icon={<ShieldAlert size={20} aria-hidden="true" />}
    >
      <NuevoProblemaForm onCancelar={onClose} onRegistrar={onRegistrar} />
    </Modal>
  )
}

function NuevoProblemaForm({
  onCancelar,
  onRegistrar,
}: {
  onCancelar: () => void
  onRegistrar: (entrada: ProblemaCrear) => Envio
}) {
  const tituloId = useId()
  const descripcionId = useId()
  const prioridadId = useId()
  const analistaId = useId()
  const [titulo, setTitulo] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [prioridad, setPrioridad] = useState<Prioridad>('media')
  const [analista, setAnalista] = useState('')
  const [errores, setErrores] = useState<Errores>({})
  const [intentos, setIntentos] = useState(0)
  const { enviando, errorEnvio, enviarAlServicio } = useEnvio()

  function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const encontrados: Errores = {}
    if (!titulo.trim()) encontrados.titulo = 'Escribe un título para el problema.'
    if (!descripcion.trim()) encontrados.descripcion = 'Describe qué está pasando.'
    setErrores(encontrados)
    if (encontrados.titulo || encontrados.descripcion) {
      setIntentos((n) => n + 1)
      return
    }
    void enviarAlServicio(() =>
      onRegistrar({
        titulo: titulo.trim(),
        descripcion: descripcion.trim(),
        prioridad,
        origen: 'manual',
        asignado_a_id: analista,
      }),
    )
  }

  return (
    <Formulario errores={errores} intentos={intentos} onSubmit={enviar}>
      <div className="space-y-4 overflow-y-auto p-5">
        <Field label="Título" htmlFor={tituloId} required error={errores.titulo}>
          <Input
            id={tituloId}
            value={titulo}
            maxLength={200}
            data-autofocus
            invalid={Boolean(errores.titulo)}
            aria-describedby={descrito(tituloId, errores.titulo)}
            placeholder="Ej. Caídas recurrentes del Wi-Fi en el edificio B"
            onChange={(event) => setTitulo(event.target.value)}
          />
        </Field>
        <Field label="Descripción" htmlFor={descripcionId} required error={errores.descripcion}>
          <Textarea
            id={descripcionId}
            value={descripcion}
            invalid={Boolean(errores.descripcion)}
            aria-describedby={descrito(descripcionId, errores.descripcion)}
            placeholder="Qué falla, desde cuándo y a quién afecta"
            onChange={(event) => setDescripcion(event.target.value)}
          />
        </Field>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Prioridad" htmlFor={prioridadId}>
            <Select
              id={prioridadId}
              value={prioridad}
              onChange={(event) => setPrioridad(event.target.value as Prioridad)}
            >
              {PRIORIDADES.map((opcion) => (
                <option key={opcion.value} value={opcion.value}>
                  {opcion.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Asignar a" htmlFor={analistaId}>
            <Select
              id={analistaId}
              value={analista}
              onChange={(event) => setAnalista(event.target.value)}
            >
              <option value="">Sin asignar</option>
              {Object.entries(ANALISTAS).map(([id, nombre]) => (
                <option key={id} value={id}>
                  {nombre}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </div>
      <Acciones
        onCancelar={onCancelar}
        accion="Registrar problema"
        enviando={enviando}
        errorEnvio={errorEnvio}
      />
    </Formulario>
  )
}

// ---------------------------------------------------------------------------------------------

interface VincularIncidenciaModalProps {
  problema: Problema | null
  onClose: () => void
  /** Devuelve el mensaje de error si no se pudo (p. ej. ya estaba vinculada). */
  onVincular: (incidenteId: string) => Envio
}

export function VincularIncidenciaModal({
  problema,
  onClose,
  onVincular,
}: VincularIncidenciaModalProps) {
  return (
    <Modal
      open={problema !== null}
      onClose={onClose}
      title="Vincular incidencia"
      description={problema ? `Agrega una incidencia a ${codigoProblema(problema.id)}` : undefined}
      icon={<Link2 size={20} aria-hidden="true" />}
    >
      <VincularForm onCancelar={onClose} onVincular={onVincular} />
    </Modal>
  )
}

function VincularForm({
  onCancelar,
  onVincular,
}: {
  onCancelar: () => void
  onVincular: (incidenteId: string) => Envio
}) {
  const incidenteId = useId()
  const [valor, setValor] = useState('')
  const [errores, setErrores] = useState<Errores>({})
  const [intentos, setIntentos] = useState(0)
  const [enviando, setEnviando] = useState(false)

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (enviando) return
    let error: string | null = 'Escribe el ID de la incidencia.'
    if (valor.trim()) {
      setEnviando(true)
      error = await onVincular(valor)
    }
    // Si salió bien, el modal se cierra y este formulario se desmonta.
    if (error) {
      setErrores({ incidente: error })
      setIntentos((n) => n + 1)
      setEnviando(false)
    }
  }

  return (
    <Formulario errores={errores} intentos={intentos} onSubmit={enviar}>
      <div className="p-5">
        <Field
          label="ID de la incidencia"
          htmlFor={incidenteId}
          required
          hint="El ID que aparece en el módulo de Incidencias."
          error={errores.incidente}
        >
          <Input
            id={incidenteId}
            value={valor}
            maxLength={64}
            data-autofocus
            invalid={Boolean(errores.incidente)}
            aria-describedby={`${incidenteId}-description`}
            placeholder="Ej. INC-000042"
            onChange={(event) => setValor(event.target.value)}
          />
        </Field>
      </div>
      <Acciones onCancelar={onCancelar} accion="Vincular incidencia" enviando={enviando} />
    </Formulario>
  )
}

// ---------------------------------------------------------------------------------------------

interface CausaRaizModalProps {
  problema: Problema | null
  onClose: () => void
  onRegistrar: (causaRaiz: string) => Envio
}

export function CausaRaizModal({ problema, onClose, onRegistrar }: CausaRaizModalProps) {
  return (
    <Modal
      open={problema !== null}
      onClose={onClose}
      title="Registrar causa raíz"
      description={problema ? `${codigoProblema(problema.id)} · ${problema.titulo}` : undefined}
      icon={<Target size={20} aria-hidden="true" />}
    >
      {problema && (
        <CausaRaizForm
          inicial={problema.causa_raiz}
          onCancelar={onClose}
          onRegistrar={onRegistrar}
        />
      )}
    </Modal>
  )
}

function CausaRaizForm({
  inicial,
  onCancelar,
  onRegistrar,
}: {
  inicial: string
  onCancelar: () => void
  onRegistrar: (causaRaiz: string) => Envio
}) {
  const causaId = useId()
  const [causa, setCausa] = useState(inicial)
  const [errores, setErrores] = useState<Errores>({})
  const [intentos, setIntentos] = useState(0)
  const { enviando, errorEnvio, enviarAlServicio } = useEnvio()

  function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!causa.trim()) {
      setErrores({ causa: 'Escribe la causa raíz para continuar.' })
      setIntentos((n) => n + 1)
      return
    }
    void enviarAlServicio(() => onRegistrar(causa.trim()))
  }

  return (
    <Formulario errores={errores} intentos={intentos} onSubmit={enviar}>
      <div className="p-5">
        <Field
          label="Causa raíz"
          htmlFor={causaId}
          required
          hint="La conclusión del análisis: el origen real de las incidencias."
          error={errores.causa}
        >
          <Textarea
            id={causaId}
            value={causa}
            data-autofocus
            invalid={Boolean(errores.causa)}
            aria-describedby={`${causaId}-description`}
            onChange={(event) => setCausa(event.target.value)}
          />
        </Field>
      </div>
      <Acciones
        onCancelar={onCancelar}
        accion="Registrar causa raíz"
        enviando={enviando}
        errorEnvio={errorEnvio}
      />
    </Formulario>
  )
}

// ---------------------------------------------------------------------------------------------

interface ErrorConocidoModalProps {
  problema: Problema | null
  onClose: () => void
  onPublicar: (entrada: ErrorConocidoCrear) => Envio
}

export function ErrorConocidoModal({ problema, onClose, onPublicar }: ErrorConocidoModalProps) {
  return (
    <Modal
      open={problema !== null}
      onClose={onClose}
      title="Publicar error conocido"
      description="La solución temporal que el Service Desk aplicará mientras se corrige la causa raíz"
      icon={<Wrench size={20} aria-hidden="true" />}
    >
      {problema && (
        <ErrorConocidoForm problema={problema} onCancelar={onClose} onPublicar={onPublicar} />
      )}
    </Modal>
  )
}

function ErrorConocidoForm({
  problema,
  onCancelar,
  onPublicar,
}: {
  problema: Problema
  onCancelar: () => void
  onPublicar: (entrada: ErrorConocidoCrear) => Envio
}) {
  const tituloId = useId()
  const workaroundId = useId()
  const articuloId = useId()
  const [titulo, setTitulo] = useState(problema.titulo)
  const [workaround, setWorkaround] = useState('')
  const [articulo, setArticulo] = useState('')
  const [errores, setErrores] = useState<Errores>({})
  const [intentos, setIntentos] = useState(0)
  const { enviando, errorEnvio, enviarAlServicio } = useEnvio()

  function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const encontrados: Errores = {}
    if (!titulo.trim()) encontrados.titulo = 'Escribe un título para el error conocido.'
    if (!workaround.trim()) encontrados.workaround = 'Explica la solución temporal.'
    setErrores(encontrados)
    if (encontrados.titulo || encontrados.workaround) {
      setIntentos((n) => n + 1)
      return
    }
    void enviarAlServicio(() =>
      onPublicar({
        problema_id: problema.id,
        titulo: titulo.trim(),
        descripcion: problema.descripcion,
        causa_raiz: problema.causa_raiz,
        workaround: workaround.trim(),
        articulo_kb_id: articulo.trim().toUpperCase(),
      }),
    )
  }

  return (
    <Formulario errores={errores} intentos={intentos} onSubmit={enviar}>
      <div className="space-y-4 overflow-y-auto p-5">
        <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-slate-700">
          <p className="text-xs font-semibold uppercase text-indigo-700">Causa raíz</p>
          <p className="mt-1">{problema.causa_raiz}</p>
        </div>
        <Field label="Título" htmlFor={tituloId} required error={errores.titulo}>
          <Input
            id={tituloId}
            value={titulo}
            maxLength={200}
            invalid={Boolean(errores.titulo)}
            aria-describedby={descrito(tituloId, errores.titulo)}
            onChange={(event) => setTitulo(event.target.value)}
          />
        </Field>
        <Field
          label="Solución temporal (workaround)"
          htmlFor={workaroundId}
          required
          error={errores.workaround}
        >
          <Textarea
            id={workaroundId}
            value={workaround}
            data-autofocus
            invalid={Boolean(errores.workaround)}
            aria-describedby={descrito(workaroundId, errores.workaround)}
            placeholder="Qué puede hacer el Service Desk para que el usuario siga trabajando"
            onChange={(event) => setWorkaround(event.target.value)}
          />
        </Field>
        <Field
          label="Artículo de la Base de Conocimiento"
          htmlFor={articuloId}
          hint="Opcional. Ej. KB-028"
        >
          <Input
            id={articuloId}
            value={articulo}
            maxLength={64}
            aria-describedby={`${articuloId}-description`}
            onChange={(event) => setArticulo(event.target.value)}
          />
        </Field>
      </div>
      <Acciones
        onCancelar={onCancelar}
        accion="Publicar error conocido"
        enviando={enviando}
        errorEnvio={errorEnvio}
      />
    </Formulario>
  )
}
