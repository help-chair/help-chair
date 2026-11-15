import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, ClipboardList, Inbox, LayoutGrid, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { CATALOG, INITIAL_REQUESTS, nextRequestId } from './data'
import { RequestForm } from './RequestForm'
import { RequestList } from './RequestList'
import { ServiceCatalog } from './ServiceCatalog'
import type { CatalogService, NewRequestInput, ServiceRequest } from './types'

type View =
  | { name: 'catalogo' }
  | { name: 'formulario'; service: CatalogService }
  | { name: 'mis-peticiones' }

/**
 * Módulo de Peticiones (Equipo 3 · Service Request Management).
 * Flujo B del prototipo: catálogo → formulario → la petición aparece en «Mis peticiones».
 * Por ahora trabaja con datos de ejemplo; se conectará a services/requests cuando exista su API.
 */
export function RequestsPage() {
  const [view, setView] = useState<View>({ name: 'catalogo' })
  const [requests, setRequests] = useState<ServiceRequest[]>(INITIAL_REQUESTS)
  const [createdId, setCreatedId] = useState<string | null>(null)
  const topRef = useRef<HTMLDivElement>(null)

  // Al cambiar de sección, vuelve arriba para que se vea el inicio (y el aviso de «¡Listo!»).
  useEffect(() => {
    topRef.current?.scrollIntoView?.({ block: 'start' })
  }, [view])

  const inProgress = requests.filter((request) => request.status !== 'completada').length
  const awaitingApproval = requests.filter(
    (request) => request.status === 'aprobacion_pendiente',
  ).length
  const completed = requests.length - inProgress

  function goTo(next: View) {
    setView(next)
    if (next.name !== 'mis-peticiones') setCreatedId(null)
  }

  function handleSubmit(service: CatalogService, input: NewRequestInput) {
    const created: ServiceRequest = {
      ...input,
      id: nextRequestId(requests),
      serviceId: service.id,
      serviceName: service.name,
      category: service.category,
      createdAt: new Date().toISOString(),
      status: service.requiresApproval ? 'aprobacion_pendiente' : 'enviada',
      requiresApproval: service.requiresApproval,
    }
    setRequests((current) => [created, ...current])
    setCreatedId(created.id)
    setView({ name: 'mis-peticiones' })
  }

  const tabs = [
    { id: 'catalogo', label: 'Catálogo de servicios', icon: LayoutGrid },
    { id: 'mis-peticiones', label: 'Mis peticiones', icon: ClipboardList, count: requests.length },
  ] as const
  const activeTab = view.name === 'mis-peticiones' ? 'mis-peticiones' : 'catalogo'

  return (
    // `relative` mantiene los textos sr-only (posición absoluta) dentro del área con scroll.
    <div
      ref={topRef}
      className="relative mx-auto w-full max-w-7xl scroll-mt-16 space-y-6 p-4 sm:p-8"
    >
      {/* Bienvenida y resumen */}
      <Card className="flex flex-col gap-5 p-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <span className="rounded-xl bg-itil-request p-3 text-white shadow-sm">
            <Inbox size={24} aria-hidden="true" />
          </span>
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-slate-900">¿Qué necesitas hoy?</h3>
            <p className="max-w-xl text-sm text-slate-600">
              Elige un servicio del catálogo, llena el formulario y sigue el avance de tu petición
              en todo momento.
            </p>
          </div>
        </div>
        <dl className="grid grid-cols-3 gap-3 lg:w-96">
          {[
            { label: 'En trámite', value: inProgress, tone: 'text-purple-700' },
            { label: 'Por aprobar', value: awaitingApproval, tone: 'text-amber-800' },
            { label: 'Completadas', value: completed, tone: 'text-emerald-700' },
          ].map((stat) => (
            <div key={stat.label} className="rounded-lg border border-border bg-slate-50 p-3">
              <dt className="text-xs font-medium text-slate-500">{stat.label}</dt>
              <dd className={cn('text-2xl font-bold', stat.tone)}>{stat.value}</dd>
            </div>
          ))}
        </dl>
      </Card>

      {/* Navegación del módulo */}
      <nav
        aria-label="Secciones de Peticiones"
        className="inline-flex flex-wrap gap-1 rounded-lg border border-border bg-white p-1 shadow-sm"
      >
        {tabs.map((tab) => {
          const active = activeTab === tab.id
          const Icon = tab.icon
          return (
            <Button
              key={tab.id}
              variant={active ? 'primary' : 'ghost'}
              size="sm"
              aria-current={active ? 'page' : undefined}
              onClick={() => goTo({ name: tab.id })}
            >
              <Icon size={16} aria-hidden="true" />
              {tab.label}
              {'count' in tab && (
                <span
                  className={cn(
                    'rounded-full px-1.5 text-xs',
                    active ? 'bg-white/20' : 'bg-slate-100 text-slate-600',
                  )}
                >
                  {tab.count}
                </span>
              )}
            </Button>
          )
        })}
      </nav>

      {createdId && view.name === 'mis-peticiones' && (
        <div
          role="status"
          className="flex items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700"
        >
          <CheckCircle2 size={20} aria-hidden="true" className="shrink-0" />
          <p className="flex-1">
            <strong>¡Listo! Tu petición {createdId} fue enviada.</strong> Aquí puedes seguir su
            avance.
          </p>
          <button
            type="button"
            aria-label="Cerrar aviso"
            onClick={() => setCreatedId(null)}
            className="rounded p-0.5 hover:bg-emerald-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      )}

      {view.name === 'catalogo' && (
        <ServiceCatalog
          services={CATALOG}
          onSelect={(service) => goTo({ name: 'formulario', service })}
        />
      )}
      {view.name === 'formulario' && (
        <RequestForm
          key={view.service.id}
          service={view.service}
          onCancel={() => goTo({ name: 'catalogo' })}
          onSubmit={(input) => handleSubmit(view.service, input)}
        />
      )}
      {view.name === 'mis-peticiones' && (
        <RequestList
          requests={requests}
          highlightId={createdId}
          onGoToCatalog={() => goTo({ name: 'catalogo' })}
        />
      )}
    </div>
  )
}
