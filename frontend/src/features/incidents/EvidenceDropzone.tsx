import { useRef, useState, type DragEvent } from 'react'
import { FileText, Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { EVIDENCE_ACCEPT, evidenceError, formatFileSize } from './data'

interface EvidenceDropzoneProps {
  id: string
  file: File | null
  error?: string
  /** Recibe el archivo válido, o `null` y el motivo por el que se rechazó. */
  onChange: (file: File | null, error?: string) => void
}

/** Zona para arrastrar o elegir la evidencia del caso (captura, log o PDF). */
export function EvidenceDropzone({ id, file, error, onChange }: EvidenceDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const labelId = `${id}-label`
  const hintId = `${id}-hint`
  const errorId = `${id}-description`

  function pick(next: File | undefined) {
    // Limpia el control para poder volver a elegir el mismo archivo.
    if (inputRef.current) inputRef.current.value = ''
    if (!next) return
    const problem = evidenceError(next)
    onChange(problem ? null : next, problem ?? undefined)
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    setDragging(false)
    pick(event.dataTransfer.files[0])
  }

  return (
    <div className="space-y-1.5">
      <p id={labelId} className="text-sm font-medium text-slate-700">
        Evidencia <span className="font-normal text-slate-500">(opcional)</span>
      </p>

      {file ? (
        <div className="flex items-center gap-3 rounded-lg border border-border bg-slate-50 px-4 py-3">
          <FileText size={20} aria-hidden="true" className="shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-800">{file.name}</p>
            <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label={`Quitar ${file.name}`}
            onClick={() => onChange(null)}
          >
            <X size={16} aria-hidden="true" />
          </Button>
        </div>
      ) : (
        <label
          htmlFor={id}
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={cn(
            'relative flex cursor-pointer flex-col items-center gap-2 rounded-lg border border-dashed bg-white px-4 py-6 text-center transition-colors hover:bg-surface-muted focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-1',
            dragging ? 'border-primary bg-primary/5' : error ? 'border-red-500' : 'border-border',
          )}
        >
          <span className="rounded-lg bg-primary/10 p-2 text-primary">
            <Upload size={16} aria-hidden="true" />
          </span>
          <span className="text-sm font-medium text-slate-700">
            Arrastra una captura, log o PDF aquí
          </span>
          <span id={hintId} className="text-xs text-slate-500">
            PNG, JPG, PDF o TXT · máx. 10 MB
          </span>
          <input
            ref={inputRef}
            id={id}
            type="file"
            accept={EVIDENCE_ACCEPT}
            className="sr-only"
            aria-labelledby={labelId}
            aria-describedby={error ? `${hintId} ${errorId}` : hintId}
            aria-invalid={Boolean(error) || undefined}
            onChange={(event) => pick(event.target.files?.[0])}
          />
        </label>
      )}

      {error && (
        <p id={errorId} className="text-xs font-medium text-red-700">
          {error}
        </p>
      )}
    </div>
  )
}
