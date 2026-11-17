import type { ReactNode } from 'react'
import { LogIn } from 'lucide-react'
import { Link } from '@/components/Link'
import { cn } from '@/lib/utils'

export const ctaClass =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary'

export const inputClass =
  'mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1'

/** Secciones de la landing a las que se puede saltar desde el encabezado. */
const LANDING_SECTIONS = [
  { id: 'que-hacemos', label: 'Qué hacemos' },
  { id: 'como-funciona', label: 'Cómo funciona' },
  { id: 'quienes-somos', label: 'Quiénes somos' },
]

function Logo() {
  return (
    <Link
      to="/"
      className="flex items-center gap-3 rounded-lg font-bold text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary"
    >
      <span
        aria-hidden="true"
        className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm text-primary-foreground shadow-sm"
      >
        HC
      </span>
      Help Chair
    </Link>
  )
}

interface PublicLayoutProps {
  children: ReactNode
  /** La landing ocupa todo el ancho y muestra los accesos a sus secciones. */
  landing?: boolean
}

export function PublicLayout({ children, landing = false }: PublicLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:shadow-md"
      >
        Saltar al contenido
      </a>

      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
          <Logo />
          {landing && (
            <nav aria-label="Secciones" className="hidden items-center gap-6 text-sm md:flex">
              {LANDING_SECTIONS.map((section) => (
                <a
                  key={section.id}
                  href={`#${section.id}`}
                  className="text-slate-600 transition-colors hover:text-slate-900"
                >
                  {section.label}
                </a>
              ))}
            </nav>
          )}
          <nav aria-label="Principal" className="flex items-center gap-2 text-sm sm:gap-3">
            <Link
              to="/entrar"
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-900"
            >
              <LogIn size={16} aria-hidden="true" />
              <span>
                Entrar<span className="sr-only sm:not-sr-only"> a mi empresa</span>
              </span>
            </Link>
            <Link to="/registro" className={ctaClass}>
              <span>
                Registrar<span className="sr-only sm:not-sr-only"> mi empresa</span>
              </span>
            </Link>
          </nav>
        </div>
      </header>

      <main id="contenido" className={cn(!landing && 'mx-auto max-w-5xl px-4 py-10')}>
        {children}
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <Logo />
            <p className="text-xs">Service Desk multiempresa alineado a ITIL v4.</p>
          </div>
          <nav aria-label="Pie de página" className="flex flex-wrap gap-x-6 gap-y-2">
            <Link to="/registro" className="hover:text-slate-900">
              Registrar mi empresa
            </Link>
            <Link to="/entrar" className="hover:text-slate-900">
              Entrar a mi empresa
            </Link>
          </nav>
          <p className="text-xs">
            Proyecto académico-profesional del CETI · {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  )
}
