import { useState } from 'react'
import { Clock, Search, SearchX, ShieldCheck, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/form'
import { cn } from '@/lib/utils'
import { CATEGORIES, getCategory } from './data'
import type { CatalogService, ServiceCategory } from './types'

interface ServiceCatalogProps {
  services: CatalogService[]
  onSelect: (service: CatalogService) => void
}

type CategoryFilter = ServiceCategory | 'todas'

function normalize(text: string) {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

/** Portal de autoservicio: tarjetas del catálogo con su SLA y si requieren aprobación. */
export function ServiceCatalog({ services, onSelect }: ServiceCatalogProps) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<CategoryFilter>('todas')

  const visible = services.filter((service) => {
    const matchesCategory = category === 'todas' || service.category === category
    const matchesQuery = normalize(`${service.name} ${service.description}`).includes(
      normalize(query.trim()),
    )
    return matchesCategory && matchesQuery
  })

  const filters: { id: CategoryFilter; label: string }[] = [
    { id: 'todas', label: 'Todas' },
    ...CATEGORIES.map(({ id, label }) => ({ id, label })),
  ]

  return (
    <section aria-labelledby="catalogo-titulo" className="space-y-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h3 id="catalogo-titulo" className="text-base font-semibold text-slate-800">
            Catálogo de servicios
          </h3>
          <p className="text-sm text-slate-600">
            Cada servicio indica cuánto tarda en entregarse y si necesita aprobación.
          </p>
        </div>
        <div className="relative w-full lg:w-72">
          <Search
            size={16}
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <Input
            type="search"
            aria-label="Buscar en el catálogo"
            placeholder="Buscar un servicio…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <div role="group" aria-label="Filtrar por categoría" className="flex flex-wrap gap-2">
        {filters.map((filter) => {
          const active = category === filter.id
          const Icon = filter.id === 'todas' ? null : getCategory(filter.id).icon
          return (
            <button
              key={filter.id}
              type="button"
              aria-pressed={active}
              onClick={() => setCategory(filter.id)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
                active
                  ? 'border-purple-200 bg-purple-50 text-purple-700'
                  : 'border-border bg-white text-slate-600 hover:bg-surface-muted',
              )}
            >
              {Icon && <Icon size={14} aria-hidden="true" />}
              {filter.label}
            </button>
          )
        })}
      </div>

      {visible.length === 0 ? (
        <Card className="flex flex-col items-center gap-3 p-10 text-center">
          <SearchX size={24} className="text-slate-400" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-slate-800">No encontramos ese servicio</p>
            <p className="text-sm text-slate-600">Prueba con otra palabra o con otra categoría.</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setQuery('')
              setCategory('todas')
            }}
          >
            Limpiar filtros
          </Button>
        </Card>
      ) : (
        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visible.map((service) => {
            const serviceCategory = getCategory(service.category)
            const Icon = serviceCategory.icon
            return (
              <li key={service.id}>
                <Card className="flex h-full flex-col p-5 transition-shadow hover:border-purple-200 hover:shadow-md">
                  <div className="flex items-start gap-3">
                    <span className="rounded-lg bg-purple-50 p-2.5 text-purple-700">
                      <Icon size={20} aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-slate-400">{serviceCategory.label}</p>
                      <h4 className="text-base font-semibold text-slate-800">{service.name}</h4>
                    </div>
                  </div>
                  <p className="mt-3 flex-1 text-sm text-slate-600">{service.description}</p>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <Badge variant="default">
                      <Clock size={12} aria-hidden="true" />
                      Entrega: {service.estimatedDelivery}
                    </Badge>
                    {service.requiresApproval ? (
                      <Badge variant="warning">
                        <ShieldCheck size={12} aria-hidden="true" />
                        Requiere aprobación
                      </Badge>
                    ) : (
                      <Badge variant="success">
                        <Zap size={12} aria-hidden="true" />
                        Sin aprobación
                      </Badge>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4 w-full"
                    aria-label={`Solicitar ${service.name}`}
                    onClick={() => onSelect(service)}
                  >
                    Solicitar
                  </Button>
                </Card>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
