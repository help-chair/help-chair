import { useState } from 'react'
import { ServiceDeskLayout, type TabKey } from '@/components/layout/ServiceDeskLayout'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { EventsPage } from '@/features/events/EventsPage'
import { RequestsPage } from '@/features/requests/RequestsPage'
import { IncidentsPage } from '@/features/incidents/IncidentsPage'
import { ProblemsPage } from '@/features/problems/ProblemsPage'
import { KnowledgePage } from '@/features/knowledge/KnowledgePage'

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')

  return (
    <ServiceDeskLayout activeTab={activeTab} onSelectTab={setActiveTab}>
      {activeTab === 'dashboard' && <DashboardPage onNavigate={setActiveTab} />}
      {activeTab === 'events' && <EventsPage />}
      {activeTab === 'requests' && <RequestsPage />}
      {activeTab === 'incidents' && <IncidentsPage />}
      {activeTab === 'problems' && <ProblemsPage />}
      {activeTab === 'knowledge' && <KnowledgePage />}
    </ServiceDeskLayout>
  )
}
