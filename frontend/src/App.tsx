import { useState } from 'react'
import { logout as cerrarSesionEnAccesos, setAccessToken } from '@/api/access'
import { ServiceDeskLayout, type TabKey } from '@/components/layout/ServiceDeskLayout'
import { useHasRole } from '@/auth/roleGuard'

import LoginPage from '@/features/access/LoginPage'
import { UsersPage } from '@/features/access/UsersPage'
import { seccionInicial, seccionesVisibles } from '@/features/access/navegacion'
import { NOMBRE_ROL } from '@/features/access/roles'
import type { Sesion } from '@/features/access/types'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { EventsPage } from '@/features/events/EventsPage'
import { RequestsPage } from '@/features/requests/RequestsPage'
import { IncidentsPage } from '@/features/incidents/IncidentsPage'
import { ProblemsPage } from '@/features/problems/ProblemsPage'
import { KnowledgePage } from '@/features/knowledge/KnowledgePage'

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')
  const [sesion, setSesion] = useState<Sesion | null>(null)

  // Hooks MUST be called unconditionally (before any early return).
  const userRole = sesion?.usuario?.rol
  const canViewRequests = useHasRole(['administrador', 'usuario_final', 'agente_n1', 'agente_n2'], userRole)

  if (!sesion) {
    return (
      <LoginPage
        onAuthenticated={(nueva) => {
          setSesion(nueva)
          setActiveTab(seccionInicial(nueva.usuario.permisos))
        }}
      />
    )
  }

  const secciones = seccionesVisibles(sesion.usuario.permisos)
  const tabActual = secciones.includes(activeTab) ? activeTab : seccionInicial(sesion.usuario.permisos)

  function salir() {
    if (sesion) void cerrarSesionEnAccesos(sesion.refresco).catch(() => undefined)
    setAccessToken(null)
    setSesion(null)
    setActiveTab('dashboard')
  }

  return (
    <ServiceDeskLayout
      activeTab={tabActual}
      onSelectTab={setActiveTab}
      usuario={{
        nombre: sesion.usuario.nombre,
        rol: NOMBRE_ROL[sesion.usuario.rol],
        rolId: sesion.usuario.rol,
      }}
      secciones={secciones}
      onLogout={salir}
    >
      {tabActual === 'dashboard' && (
        <DashboardPage onNavigate={setActiveTab} secciones={secciones} rolId={sesion.usuario.rol} />
      )}
      {tabActual === 'events' && <EventsPage />}
      {tabActual === 'requests' && (
        canViewRequests ? (
          <RequestsPage
            puedeGestionar={sesion.usuario.permisos.includes('tickets:atender')}
          />
        ) : (
          <div className="p-4 text-center text-red-600">No tienes permiso para ver solicitudes.</div>
        )
      )}
      {tabActual === 'access' && <UsersPage usuario={sesion.usuario} />}
      {tabActual === 'incidents' && <IncidentsPage />}
      {tabActual === 'problems' && <ProblemsPage />}
      {tabActual === 'knowledge' && <KnowledgePage />}
    </ServiceDeskLayout>
  )
}
