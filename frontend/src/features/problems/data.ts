import type { BadgeProps } from '@/components/ui/badge'
import type { EstadoProblema, Origen, Prioridad, Problema } from './types'

// Catálogos y utilidades del módulo. Los problemas, vínculos y errores conocidos vienen siempre
// de services/problems (contracts/problems/openapi.yaml): aquí no hay datos de ejemplo.

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
