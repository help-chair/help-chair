import { useState, type FormEvent } from 'react'
import { ArrowRight, CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getRuntimeConfig } from '@/config/runtime'
import { navigate } from '@/lib/routing'
import { cn } from '@/lib/utils'
import { AVAILABILITY_TEXT, BLOCKING, slugify, useSubdomainAvailability } from './subdomain'

/**
 * «Elige tu subdominio»: comprueba la disponibilidad mientras se escribe y lleva al registro
 * con el subdominio ya capturado (/registro?subdominio=…).
 */
export function SubdomainClaim() {
  const [subdominio, setSubdominio] = useState('')
  const [availability] = useSubdomainAvailability(subdominio)
  const baseDomain = getRuntimeConfig().baseDomain
  const blocked = BLOCKING.includes(availability)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (blocked) return
    navigate(subdominio ? `/registro?subdominio=${encodeURIComponent(subdominio)}` : '/registro')
  }

  const StatusIcon =
    availability === 'ok' ? CheckCircle2 : availability === 'checking' ? Loader2 : XCircle

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-2" noValidate>
      <label htmlFor="landing-subdominio" className="block text-sm font-medium text-slate-700">
        Elige el subdominio de tu empresa
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
        <div
          className={cn(
            'flex h-12 w-full items-center rounded-lg border bg-white shadow-sm transition-colors focus-within:ring-2 focus-within:ring-offset-1 sm:flex-1',
            blocked
              ? 'border-red-500 focus-within:ring-itil-exception'
              : 'border-slate-300 focus-within:ring-ring',
          )}
        >
          <input
            id="landing-subdominio"
            value={subdominio}
            onChange={(event) => setSubdominio(slugify(event.target.value))}
            placeholder="tuempresa"
            autoComplete="off"
            spellCheck={false}
            maxLength={30}
            aria-invalid={blocked || undefined}
            aria-describedby="landing-subdominio-estado"
            className="h-full min-w-0 flex-1 rounded-l-lg bg-transparent pl-4 text-base text-slate-900 placeholder:text-slate-400 focus:outline-none"
          />
          <span className="whitespace-nowrap pr-4 text-base text-slate-500">.{baseDomain}</span>
        </div>
        <Button type="submit" size="lg" disabled={blocked} className="shrink-0">
          Comenzar registro
          <ArrowRight size={16} aria-hidden="true" />
        </Button>
      </div>
      <p
        id="landing-subdominio-estado"
        role="status"
        aria-live="polite"
        className={cn(
          'flex min-h-5 items-center gap-1.5 text-xs font-medium',
          availability === 'ok' && 'text-emerald-700',
          availability === 'checking' && 'text-slate-500',
          (blocked || availability === 'error') && 'text-red-700',
        )}
      >
        {availability === 'idle' ? (
          <span className="font-normal text-slate-500">
            Será la dirección de tu help desk. La podrás usar en cuanto termine el registro.
          </span>
        ) : (
          <>
            <StatusIcon
              size={14}
              aria-hidden="true"
              className={cn(availability === 'checking' && 'animate-spin')}
            />
            {AVAILABILITY_TEXT[availability]}
          </>
        )}
      </p>
    </form>
  )
}
