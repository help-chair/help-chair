import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

// Controles de formulario del UI Kit (Figma · Form Controls: Default, Focus, Error).

const controlBase =
  'w-full rounded-lg border bg-white px-3 text-sm text-slate-800 placeholder:text-slate-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-slate-500'

function controlState(invalid?: boolean) {
  return invalid
    ? 'border-red-500 focus-visible:ring-itil-exception' // ≥ 3:1 de contraste (WCAG 1.4.11)
    : 'border-border focus-visible:ring-ring'
}

interface ControlProps {
  /** Marca el control en estado de error (borde rojo y aria-invalid). */
  invalid?: boolean
}

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & ControlProps
>(({ className, invalid, ...props }, ref) => (
  <input
    ref={ref}
    aria-invalid={invalid || undefined}
    className={cn(controlBase, controlState(invalid), 'h-10', className)}
    {...props}
  />
))
Input.displayName = 'Input'

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & ControlProps
>(({ className, invalid, rows = 4, ...props }, ref) => (
  <textarea
    ref={ref}
    rows={rows}
    aria-invalid={invalid || undefined}
    className={cn(controlBase, controlState(invalid), 'py-2 resize-y', className)}
    {...props}
  />
))
Textarea.displayName = 'Textarea'

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement> & ControlProps
>(({ className, invalid, children, ...props }, ref) => (
  <div className="relative">
    <select
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(controlBase, controlState(invalid), 'h-10 appearance-none pr-9', className)}
      {...props}
    >
      {children}
    </select>
    <ChevronDown
      size={16}
      aria-hidden="true"
      className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
    />
  </div>
))
Select.displayName = 'Select'

interface FieldProps {
  label: string
  htmlFor: string
  required?: boolean
  hint?: string
  error?: string
  className?: string
  children: React.ReactNode
}

/**
 * Envuelve un control con su etiqueta, ayuda y mensaje de error.
 * El mensaje usa el id `${htmlFor}-description`: pásalo al control en `aria-describedby`.
 */
export function Field({ label, htmlFor, required, hint, error, className, children }: FieldProps) {
  const message = error ?? hint
  return (
    <div className={cn('space-y-1.5', className)}>
      <label htmlFor={htmlFor} className="block text-sm font-medium text-slate-700">
        {label}
        {required && (
          <span className="text-red-600" aria-hidden="true">
            {' '}
            *
          </span>
        )}
      </label>
      {children}
      {message && (
        <p
          id={`${htmlFor}-description`}
          className={cn('text-xs', error ? 'font-medium text-red-700' : 'text-slate-500')}
        >
          {message}
        </p>
      )}
    </div>
  )
}
