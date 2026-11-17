import { Suspense, lazy } from 'react'
import { currentSite } from '@/config/runtime'
import { usePath } from '@/lib/routing'

// Dos conjuntos de rutas con carga diferida: el sitio público no pesa en el Service Desk y viceversa.
const PublicSite = lazy(() => import('@/features/public/PublicSite'))
const ServiceDesk = lazy(() => import('@/App'))
const ActivatePage = lazy(() => import('@/features/desk/ActivatePage'))

export default function Root() {
  const path = usePath()
  const site = currentSite()

  return (
    <Suspense fallback={<p className="p-8 text-sm text-slate-500">Cargando…</p>}>
      {site.mode === 'public' ? (
        <PublicSite path={path} />
      ) : path === '/activar' ? (
        <ActivatePage />
      ) : (
        <ServiceDesk />
      )}
    </Suspense>
  )
}
