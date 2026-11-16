import type { EventItem } from './types'

export const INITIAL_EVENTS: EventItem[] = [
  {
    id: 'EVT-1049',
    timestamp: '11:15:02',
    type: 'exception',
    title: 'Fallo de conexión en Gateway de Pagos - Timeout > 5000ms',
    source: 'Infraestructura / API',
    destination: 'Incidencias (P1 - Crítico)',
    status: 'Enrutado a Incidencias',
  },
  {
    id: 'EVT-1048',
    timestamp: '11:10:45',
    type: 'warning',
    title: 'Espacio en disco > 85% en nodo de base de datos bd-cluster-02',
    source: 'Monitoring Agent',
    destination: 'Registro y vigilancia',
    status: 'Bajo observación',
  },
  {
    id: 'EVT-1047',
    timestamp: '11:02:18',
    type: 'informational',
    title: 'Solicitud de acceso a VPN para nuevo colaborador',
    source: 'Portal de autoservicio',
    destination: 'Peticiones (Catálogo)',
    status: 'Enrutado a Peticiones',
  },
  {
    id: 'EVT-1046',
    timestamp: '10:55:00',
    type: 'informational',
    title: 'Copia de seguridad incremental completada satisfactoriamente',
    source: 'Cron Backup Service',
    destination: 'Solo registro',
    status: 'Cerrado automático',
  },
  {
    id: 'EVT-1045',
    timestamp: '10:48:12',
    type: 'exception',
    title: 'Intentos fallidos de autenticación reiterados (5 intentos en 1 min)',
    source: 'Servicio de Accesos',
    destination: 'Seguridad / Accesos',
    status: 'Enrutado a Accesos',
  },
]
