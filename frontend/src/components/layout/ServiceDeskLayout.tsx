import type { ReactNode } from 'react'
import {
  Activity,
  Bell,
  BookOpen,
  Flame,
  Inbox,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Server,
  ShieldAlert,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { RolId } from '@/features/access/types'

export type TabKey =
  | 'dashboard'
  | 'events'
  | 'requests'
  | 'incidents'
  | 'problems'
  | 'knowledge'
  | 'access'

/** Lo mínimo que el cascarón necesita de la sesión; lo entrega Accesos desde `App.tsx`. */
interface UsuarioDeSesion {
  nombre: string
  rol: string
  /** Identificador del rol para personalizar textos (p. ej. el título del dashboard). */
  rolId?: RolId
}

interface ServiceDeskLayoutProps {
  activeTab: TabKey
  onSelectTab: (tab: TabKey) => void
  /** Sesión activa. Si falta, el header muestra el usuario de ejemplo. */
  usuario?: UsuarioDeSesion
  /**
   * Secciones que el rol de la sesión puede ver (navegación según rol).
   * Las calcula Accesos en `features/access/navegacion.ts`. Si falta, se muestran todas.
   */
  secciones?: TabKey[]
  onLogout?: () => void
  children: ReactNode
}

export function ServiceDeskLayout({
  activeTab,
  onSelectTab,
  usuario,
  secciones,
  onLogout,
  children,
}: ServiceDeskLayoutProps) {
  const puedeVer = (seccion: TabKey) => secciones === undefined || secciones.includes(seccion)

  const puedeOperar = puedeVer('events') || puedeVer('incidents') || puedeVer('problems')
  const puedeAdministrar = puedeVer('access')

  const getHeaderTitle = () => {
    switch (activeTab) {
      case 'dashboard':
        return usuario?.rolId === 'usuario_final'
          ? 'Mi espacio'
          : 'Service Desk · Vista Operativa'
      case 'events':
        return 'Consola de Monitoreo de Eventos'
      case 'requests':
        return 'Gestión de Peticiones de Servicio'
      case 'incidents':
        return 'Gestión de Incidencias'
      case 'problems':
        return 'Gestión de Problemas'
      case 'knowledge':
        return 'Base de Conocimiento (KB)'
      case 'access':
        return 'Gestión de Accesos'
      default:
        return 'Service Desk'
    }
  }

  const iniciales = (usuario?.nombre ?? 'Admin Help Desk')
    .split(' ')
    .map((parte) => parte[0] ?? '')
    .slice(0, 2)
    .join('')
    .toUpperCase()

  const claseBoton = (activo: boolean) =>
    `w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      activo
        ? 'bg-indigo-600 text-white shadow-sm'
        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
    }`

  const etiquetaGrupo = 'px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400'

  return (
    <div className="flex h-screen bg-slate-100 text-slate-800">
      {/* Sidebar de navegación */}
      <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col justify-between shadow-xl shrink-0">
        <div>
          {/* Logo y contexto de la empresa */}
          <div className="p-5 border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md">
                HC
              </div>
              <div>
                <h1 className="font-bold text-base text-white tracking-wide">Help Chair</h1>
                <p className="text-xs text-slate-400">ITIL v4 Service Desk</p>
              </div>
            </div>
            <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-indigo-300 border border-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              {window.location.host}
            </div>
          </div>

          {/* Menú principal */}
          <nav aria-label="Secciones del Service Desk" className="p-4 space-y-1">
            <p className={etiquetaGrupo}>Mi espacio</p>
            <button
              onClick={() => onSelectTab('dashboard')}
              aria-current={activeTab === 'dashboard' ? 'page' : undefined}
              className={claseBoton(activeTab === 'dashboard')}
            >
              <LayoutDashboard size={18} />
              Dashboard Principal
            </button>
            {puedeVer('requests') && (
              <button
                onClick={() => onSelectTab('requests')}
                aria-current={activeTab === 'requests' ? 'page' : undefined}
                className={claseBoton(activeTab === 'requests')}
              >
                <Inbox size={18} className={activeTab === 'requests' ? '' : 'text-purple-400'} />
                <span>Peticiones</span>
              </button>
            )}
            {puedeVer('knowledge') && (
              <button
                onClick={() => onSelectTab('knowledge')}
                aria-current={activeTab === 'knowledge' ? 'page' : undefined}
                className={claseBoton(activeTab === 'knowledge')}
              >
                <BookOpen size={18} className={activeTab === 'knowledge' ? '' : 'text-emerald-400'} />
                <span>Base de Conocimiento</span>
              </button>
            )}

            {puedeOperar && (
              <>
                <p className={`pt-4 ${etiquetaGrupo}`}>Operación</p>
                {puedeVer('events') && (
                  <button
                    onClick={() => onSelectTab('events')}
                    aria-current={activeTab === 'events' ? 'page' : undefined}
                    className={claseBoton(activeTab === 'events')}
                  >
                    <Activity size={18} />
                    Gestión de Eventos
                  </button>
                )}
                {puedeVer('incidents') && (
                  <button
                    onClick={() => onSelectTab('incidents')}
                    aria-current={activeTab === 'incidents' ? 'page' : undefined}
                    className={claseBoton(activeTab === 'incidents')}
                  >
                    <Flame size={18} className={activeTab === 'incidents' ? '' : 'text-red-400'} />
                    <span>Incidencias</span>
                  </button>
                )}
                {puedeVer('problems') && (
                  <button
                    onClick={() => onSelectTab('problems')}
                    aria-current={activeTab === 'problems' ? 'page' : undefined}
                    className={claseBoton(activeTab === 'problems')}
                  >
                    <ShieldAlert
                      size={18}
                      className={activeTab === 'problems' ? '' : 'text-amber-400'}
                    />
                    <span>Problemas</span>
                  </button>
                )}
              </>
            )}

            {puedeAdministrar && (
              <>
                <p className={`pt-4 ${etiquetaGrupo}`}>Administración</p>
                {puedeVer('access') && (
                  <button
                    onClick={() => onSelectTab('access')}
                    aria-current={activeTab === 'access' ? 'page' : undefined}
                    className={claseBoton(activeTab === 'access')}
                  >
                    <KeyRound size={18} className={activeTab === 'access' ? '' : 'text-indigo-300'} />
                    <span>Accesos</span>
                  </button>
                )}
              </>
            )}
          </nav>
        </div>

        {/* Footer del sidebar */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-3 py-2 text-sm text-slate-400">
            <Server size={16} />
            <span className="text-xs">Stack: K8s Namespace Activo</span>
          </div>
        </div>
      </aside>

      {/* Contenedor Principal */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        {/* Header superior */}
        <header className="h-16 bg-white border-b border-border px-8 flex items-center justify-between sticky top-0 z-10 shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-800">{getHeaderTitle()}</h2>
            <Badge variant="outline">Gateway del Stack</Badge>
          </div>

          <div className="flex items-center gap-4">
            <button
              type="button"
              className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-surface-muted rounded-full transition-colors"
            >
              <Bell size={18} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white"></span>
            </button>
            <div className="flex items-center gap-2 pl-4 border-l border-border">
              <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center font-medium text-xs">
                {iniciales}
              </div>
              <div className="text-left text-xs">
                <p className="font-semibold text-slate-700">{usuario?.nombre ?? 'Admin Help Desk'}</p>
                <p className="text-slate-500">{usuario?.rol ?? 'Service Desk Lead'}</p>
              </div>
              {onLogout && (
                <Button variant="ghost" size="sm" className="ml-2" onClick={onLogout}>
                  <LogOut size={16} aria-hidden="true" />
                  Salir
                </Button>
              )}
            </div>
          </div>
        </header>

        {/* Cuerpo de la vista activa */}
        <div className="p-8 max-w-7xl mx-auto w-full">{children}</div>
      </main>
    </div>
  )
}
