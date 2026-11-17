export type EventSeverity = 'informational' | 'warning' | 'exception'

export interface EventItem {
  id: string
  timestamp: string
  type: EventSeverity
  title: string
  source: string
  destination: string
  status: string
}
