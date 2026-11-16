import type { ReactNode } from 'react'
import { Link } from '@/components/Link'

export const ctaClass =
  'inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2'

export const inputClass =
  'mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1'

export function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-3 font-bold text-slate-900">
            <span
              aria-hidden="true"
              className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm text-primary-foreground"
            >
              HC
            </span>
            Help Chair
          </Link>
          <nav aria-label="Principal" className="flex items-center gap-4 text-sm">
            <Link to="/entrar" className="text-slate-600 hover:text-slate-900">
              Entrar a mi empresa
            </Link>
            <Link to="/registro" className={ctaClass}>
              Registrar mi empresa
            </Link>
          </nav>
        </div>
      </header>
      <main id="contenido" className="mx-auto max-w-5xl px-4 py-10">
        {children}
      </main>
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        Help Chair · Proyecto académico-profesional del CETI
      </footer>
    </div>
  )
}
