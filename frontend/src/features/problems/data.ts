import type { BadgeProps } from '@/components/ui/badge'
import type {
  DatosProblemas,
  ErrorConocido,
  EstadoProblema,
  Origen,
  Prioridad,
  Problema,
  ProblemaIncidente,
} from './types'

// Catálogos, datos de ejemplo (mocks) y utilidades del módulo mientras services/problems
// publica su API. Los casos son los del diseño (frontend/docs/problems/).

export type BadgeVariant = NonNullable<BadgeProps['variant']>

export interface Opcion<T extends string> {
  value: T
  label: string
  variant: BadgeVariant
}

/** Ciclo de vida del contrato, en orden: registrado → … → cerrado. */
export const ESTADOS: Opcion<EstadoProblema>[] = [
  { value: 'registrado', label: 'Registrado', variant: 'default' },
  { value: 'en_analisis', label: 'En análisis', variant: 'info' },
  { value: 'causa_identificada', label: 'Causa identificada', variant: 'info' },
  { value: 'error_conocido', label: 'Error conocido', variant: 'warning' },
  { value: 'resuelto', label: 'Resuelto', variant: 'success' },
  { value: 'cerrado', label: 'Cerrado', variant: 'outline' },
]

export const PRIORIDADES: Opcion<Prioridad>[] = [
  { value: 'critica', label: 'Crítica', variant: 'exception' },
  { value: 'alta', label: 'Alta', variant: 'warning' },
  { value: 'media', label: 'Media', variant: 'info' },
  { value: 'baja', label: 'Baja', variant: 'default' },
]

export const ORIGENES: Opcion<Origen>[] = [
  { value: 'patron', label: 'Patrón detectado', variant: 'info' },
  { value: 'manual', label: 'Manual', variant: 'default' },
]

export function buscarOpcion<T extends string>(opciones: Opcion<T>[], value: T) {
  return opciones.find((opcion) => opcion.value === value) ?? opciones[0]
}

export const TONO_PUNTO: Record<BadgeVariant, string> = {
  default: 'bg-slate-400',
  outline: 'bg-slate-500',
  info: 'bg-itil-info',
  warning: 'bg-itil-warning',
  exception: 'bg-itil-exception',
  success: 'bg-itil-success',
  request: 'bg-itil-request',
}

/** Siguiente estado del ciclo de vida, o `null` si el problema ya está cerrado. */
export function siguienteEstado(estado: EstadoProblema): EstadoProblema | null {
  const indice = ESTADOS.findIndex((opcion) => opcion.value === estado)
  return ESTADOS[indice + 1]?.value ?? null
}

/** Botón que avanza a cada estado y el aviso que lo confirma (con el mismo verbo). */
export const AVANCES: Record<
  Exclude<EstadoProblema, 'registrado'>,
  { boton: string; aviso: (codigo: string) => string }
> = {
  en_analisis: { boton: 'Iniciar análisis', aviso: (codigo) => `Análisis iniciado en ${codigo}.` },
  causa_identificada: {
    boton: 'Registrar causa raíz',
    aviso: (codigo) => `Causa raíz registrada en ${codigo}.`,
  },
  error_conocido: {
    boton: 'Publicar error conocido',
    aviso: (codigo) => `Error conocido publicado para ${codigo}.`,
  },
  resuelto: {
    boton: 'Marcar como resuelto',
    aviso: (codigo) => `${codigo} marcado como resuelto.`,
  },
  cerrado: { boton: 'Cerrar problema', aviso: (codigo) => `${codigo} cerrado.` },
}

/** El contrato pide `causa_raiz` para pasar a estos estados. */
export function requiereCausaRaiz(estado: EstadoProblema) {
  return estado === 'causa_identificada' || estado === 'error_conocido'
}

export function estaAbierto(problema: Problema) {
  return problema.estado !== 'resuelto' && problema.estado !== 'cerrado'
}

export function codigoProblema(id: number) {
  return `PRB-${String(id).padStart(3, '0')}`
}

export function codigoError(id: number) {
  return `KE-${String(id).padStart(3, '0')}`
}

/** Nombres de las personas de Accesos (mismos IDs que features/access/data.ts). */
export const ANALISTAS: Record<string, string> = {
  'usr-003': 'Marco Estrada',
  'usr-002': 'Daniela Ruiz',
  'usr-006': 'Sofía Marín',
}

/**
 * Descripción de algunas incidencias para mostrarlas en el detalle. El contrato de Problemas
 * solo guarda el ID; la descripción la dará services/incidents.
 */
export const INCIDENCIAS: Record<string, string> = {
  'TCK-1045': 'Wi-Fi caído en el edificio B',
  'TCK-1039': 'Sin internet en el salón B-12',
  'TCK-1031': 'Wi-Fi lento en el laboratorio B-4',
  'TCK-1027': 'Desconexión durante un examen en línea',
  'TCK-1022': 'Proyector inalámbrico sin red en B-8',
  'TCK-1018': 'Wi-Fi caído en el edificio B',
  'TCK-1012': 'Equipos del salón B-3 sin conexión',
  'TCK-1046': 'Servidor de base de datos caído',
  'TCK-1044': 'Correo institucional no envía mensajes',
  'TCK-1048': 'Impresora del laboratorio no responde',
}

const formatoFecha = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'short' })

/** «14 nov» */
export function formatFecha(iso: string) {
  return formatoFecha.format(new Date(iso)).replace('.', '')
}

function problema(datos: Omit<Problema, 'actualizado_en' | 'resuelto_en'> & Partial<Problema>) {
  return { actualizado_en: datos.creado_en, resuelto_en: null, ...datos } satisfies Problema
}

function vinculos(problemaId: number, ids: string[], desde: string): ProblemaIncidente[] {
  return ids.map((incidenteId, indice) => ({
    id: problemaId * 100 + indice,
    problema_id: problemaId,
    incidente_id: incidenteId,
    vinculado_en: desde,
  }))
}

/** Datos de ejemplo frescos (cada llamada devuelve copias nuevas). */
export function crearDatosDeEjemplo(): DatosProblemas {
  const problemas: Problema[] = [
    problema({
      id: 16,
      titulo: 'Correo institucional rechaza adjuntos grandes',
      descripcion: 'Los envíos con archivos de más de 10 MB rebotan sin aviso.',
      estado: 'en_analisis',
      prioridad: 'alta',
      origen: 'patron',
      causa_raiz: '',
      asignado_a_id: 'usr-002',
      creado_en: '2026-11-18T16:20:00Z',
    }),
    problema({
      id: 15,
      titulo: 'Caídas recurrentes del Wi-Fi en el edificio B',
      descripcion:
        'El sistema detectó 7 incidencias de desconexión del Wi-Fi en el edificio B en 14 días. Todas ocurrieron entre las 10:00 y las 13:00, en el horario con más grupos en clase.',
      estado: 'error_conocido',
      prioridad: 'critica',
      origen: 'patron',
      causa_raiz:
        'Capacidad insuficiente de la red del edificio B: un solo punto de acceso para más de 80 dispositivos.',
      asignado_a_id: 'usr-003',
      creado_en: '2026-11-03T15:14:00Z',
      actualizado_en: '2026-11-09T18:40:00Z',
    }),
    problema({
      id: 14,
      titulo: 'Saturación de disco en bd-cluster-02',
      descripcion: 'El nodo pasa de 85 % de uso y tumba el servidor de base de datos.',
      estado: 'error_conocido',
      prioridad: 'critica',
      origen: 'patron',
      causa_raiz: 'Los logs de réplica nunca se depuran y llenan el volumen.',
      asignado_a_id: 'usr-002',
      creado_en: '2026-11-17T17:05:00Z',
    }),
    problema({
      id: 13,
      titulo: 'Impresoras del laboratorio pierden conexión',
      descripcion: 'Pasa después de cada actualización de Windows.',
      estado: 'registrado',
      prioridad: 'media',
      origen: 'manual',
      causa_raiz: '',
      asignado_a_id: '',
      creado_en: '2026-11-17T19:30:00Z',
    }),
    problema({
      id: 12,
      titulo: 'Timeout en el Gateway de Pagos en horas pico',
      descripcion: 'Las operaciones tardan más de 5000 ms entre las 12:00 y las 14:00.',
      estado: 'causa_identificada',
      prioridad: 'alta',
      origen: 'patron',
      causa_raiz:
        'El pool de conexiones del gateway se agota cuando hay más de 200 cobros por minuto.',
      asignado_a_id: 'usr-003',
      creado_en: '2026-11-14T18:00:00Z',
    }),
    problema({
      id: 11,
      titulo: 'Sesiones del sistema escolar expiran antes de tiempo',
      descripcion: 'Los usuarios perdían la sesión a los 5 minutos.',
      estado: 'resuelto',
      prioridad: 'media',
      origen: 'manual',
      causa_raiz: 'El tiempo de sesión estaba configurado en 5 minutos en lugar de 60.',
      asignado_a_id: 'usr-006',
      creado_en: '2026-11-10T16:45:00Z',
      actualizado_en: '2026-11-16T17:00:00Z',
      resuelto_en: '2026-11-16T17:00:00Z',
    }),
  ]

  const incidentes: ProblemaIncidente[] = [
    ...vinculos(
      16,
      ['TCK-1044', 'TCK-1037', 'TCK-1033', 'TCK-1029', 'TCK-1020'],
      '2026-11-18T16:20:00Z',
    ),
    ...vinculos(
      15,
      ['TCK-1045', 'TCK-1039', 'TCK-1031', 'TCK-1027', 'TCK-1022', 'TCK-1018', 'TCK-1012'],
      '2026-11-03T15:14:00Z',
    ),
    ...vinculos(14, ['TCK-1046', 'TCK-1035', 'TCK-1024', 'TCK-1015'], '2026-11-17T17:05:00Z'),
    ...vinculos(13, ['TCK-1048', 'TCK-1041', 'TCK-1036'], '2026-11-17T19:30:00Z'),
    ...vinculos(
      12,
      [
        'TCK-1043',
        'TCK-1040',
        'TCK-1034',
        'TCK-1030',
        'TCK-1026',
        'TCK-1021',
        'TCK-1017',
        'TCK-1013',
        'TCK-1010',
      ],
      '2026-11-14T18:00:00Z',
    ),
    ...vinculos(
      11,
      ['TCK-1038', 'TCK-1032', 'TCK-1028', 'TCK-1023', 'TCK-1019', 'TCK-1011'],
      '2026-11-10T16:45:00Z',
    ),
  ]

  const errores: ErrorConocido[] = [
    {
      id: 7,
      problema_id: 14,
      titulo: 'Disco lleno en bd-cluster-02',
      descripcion: 'El servidor de base de datos deja de responder cuando el disco se llena.',
      causa_raiz: 'Los logs de réplica nunca se depuran y llenan el volumen.',
      workaround:
        'Ejecutar el script de limpieza de logs y reiniciar la réplica. Libera cerca de 20 % del disco.',
      articulo_kb_id: 'KB-031',
      activo: true,
      creado_en: '2026-11-18T15:00:00Z',
      actualizado_en: '2026-11-18T15:00:00Z',
    },
    {
      id: 6,
      problema_id: 15,
      titulo: 'El Wi-Fi del edificio B se desconecta',
      descripcion: 'Los equipos pierden internet entre las 10:00 y las 13:00.',
      causa_raiz: 'Un solo punto de acceso para más de 80 dispositivos.',
      workaround:
        'Conectar los equipos a la red de respaldo CETI-B-2 mientras se instala el segundo punto de acceso.',
      articulo_kb_id: 'KB-028',
      activo: true,
      creado_en: '2026-11-09T18:40:00Z',
      actualizado_en: '2026-11-09T18:40:00Z',
    },
    {
      id: 4,
      problema_id: 11,
      titulo: 'La sesión del sistema escolar expira sola',
      descripcion: 'La sesión se cierra a los 5 minutos de inactividad.',
      causa_raiz: 'El tiempo de sesión estaba configurado en 5 minutos.',
      workaround: 'Guardar el trabajo seguido y volver a iniciar sesión.',
      articulo_kb_id: '',
      activo: false,
      creado_en: '2026-11-12T16:00:00Z',
      actualizado_en: '2026-11-16T17:00:00Z',
    },
  ]

  const analisis: DatosProblemas['analisis'] = {
    15: [
      {
        pregunta: '¿Por qué se cae el Wi-Fi del edificio B?',
        respuesta: 'Los equipos pierden la conexión con el punto de acceso AP-B1.',
      },
      {
        pregunta: '¿Por qué pierden la conexión con AP-B1?',
        respuesta: 'El punto de acceso se reinicia solo varias veces al día.',
      },
      {
        pregunta: '¿Por qué se reinicia solo?',
        respuesta: 'Se sobrecalienta cuando pasa de 80 dispositivos conectados.',
      },
      {
        pregunta: '¿Por qué pasa de 80 dispositivos?',
        respuesta:
          'En horario de clases se juntan 3 grupos en el mismo piso y no hay otro punto de acceso cerca.',
      },
      {
        pregunta: '¿Por qué no hay otro punto de acceso?',
        respuesta: 'La red del edificio se diseñó para 40 usuarios y nunca se amplió.',
      },
    ],
    14: [
      {
        pregunta: '¿Por qué se cae el servidor de base de datos?',
        respuesta: 'El disco del nodo bd-cluster-02 se llena.',
      },
      {
        pregunta: '¿Por qué se llena el disco?',
        respuesta: 'Los logs de réplica ocupan casi todo el volumen.',
      },
      {
        pregunta: '¿Por qué ocupan tanto los logs?',
        respuesta: 'Nunca se depuran: no hay una tarea programada que borre los viejos.',
      },
    ],
  }

  return { problemas, incidentes, errores, analisis }
}

/**
 * Simula la respuesta de services/problems. Cuando exista la API, se reemplaza por las
 * llamadas en src/api/ y la pantalla no cambia.
 */
export function cargarDatosDeEjemplo(): Promise<DatosProblemas> {
  return new Promise((resolve) => setTimeout(() => resolve(crearDatosDeEjemplo()), 300))
}
