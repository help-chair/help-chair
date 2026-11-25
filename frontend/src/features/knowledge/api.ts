// Integración del módulo de Base de Conocimiento con services/knowledge.
// Llama a la API real y, si el servicio no responde, usa los artículos de ejemplo.
import { ApiError } from '@/api/client'
import { listarArticulos, type ArticuloContrato } from '@/api/knowledge'
import { crearArticulosDeEjemplo } from './data'
import type { Articulo, Categoria } from './types'

function servicioInalcanzable(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 404 || error.status >= 500
  return true
}

const CATEGORIAS_VALIDAS = new Set<Categoria>([
  'red',
  'accesos',
  'correo',
  'impresoras',
  'software',
  'base_datos',
])

function normalizarCategoria(categoria: string | null): Categoria {
  if (categoria && CATEGORIAS_VALIDAS.has(categoria as Categoria)) {
    return categoria as Categoria
  }
  return 'software'
}

function articuloContratoAUI(item: ArticuloContrato): Articulo {
  const lineas = item.contenido
    .split('\n')
    .map((linea) => linea.trim())
    .filter(Boolean)

  return {
    id: item.id,
    titulo: item.titulo || 'Artículo sin título',
    resumen: lineas[0] ?? 'Sin resumen disponible.',
    categoria: normalizarCategoria(item.categoria),
    visibilidad: item.visibilidad === 'empresa' ? 'publico' : 'agentes',
    error_conocido_id: null,
    sintomas: [],
    pasos: lineas.length > 1 ? lineas.slice(1) : lineas,
    si_no_funciona: 'Si el problema persiste, registra una incidencia con el Service Desk.',
    autor: item.autor_id ?? 'Equipo de Soporte',
    actualizado_en: item.actualizado_en,
    consultas: 0,
    votos_utiles: 0,
    votos_no_utiles: 0,
  }
}

export async function cargarArticulosConRespaldo(): Promise<Articulo[]> {
  try {
    const pagina = await listarArticulos()
    return pagina.results.map(articuloContratoAUI)
  } catch (error) {
    if (!servicioInalcanzable(error)) throw error
    return crearArticulosDeEjemplo()
  }
}
