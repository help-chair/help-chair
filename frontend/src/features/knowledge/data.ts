import type { Articulo, Categoria } from './types'

// Catálogos y utilidades del módulo. Los artículos vienen siempre de services/knowledge
// (contracts/knowledge/openapi.yaml): aquí no hay datos de ejemplo.

export const CATEGORIAS: { value: Categoria; label: string }[] = [
  { value: 'red', label: 'Red y Wi-Fi' },
  { value: 'accesos', label: 'Accesos y contraseñas' },
  { value: 'correo', label: 'Correo' },
  { value: 'impresoras', label: 'Impresoras' },
  { value: 'software', label: 'Software' },
  { value: 'base_datos', label: 'Base de datos' },
]

export function nombreCategoria(categoria: Categoria) {
  return CATEGORIAS.find((opcion) => opcion.value === categoria)?.label ?? categoria
}

/** Por debajo de este porcentaje, el artículo aparece en «Necesitan mejora». */
export const UMBRAL_MEJORA = 80

export function porcentajeUtil(articulo: Articulo) {
  const total = articulo.votos_utiles + articulo.votos_no_utiles
  return total === 0 ? 0 : Math.round((articulo.votos_utiles / total) * 100)
}

export function codigoError(id: number) {
  return `KE-${String(id).padStart(3, '0')}`
}

const formatoFecha = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'short' })

/** «12 nov» */
export function formatFecha(iso: string) {
  return formatoFecha.format(new Date(iso)).replace('.', '')
}

/** Minúsculas, sin acentos ni guiones: «contrasena» encuentra «contraseña» y «wifi», «Wi-Fi». */
function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/-/g, '').toLowerCase()
}

/** Palabras que no ayudan a encontrar un artículo («no tengo wifi en el edificio» → wifi, edificio). */
const PALABRAS_VACIAS = new Set([
  'como',
  'con',
  'cuando',
  'del',
  'esta',
  'este',
  'las',
  'los',
  'mas',
  'mis',
  'para',
  'pero',
  'por',
  'puedo',
  'que',
  'sin',
  'tengo',
  'una',
  'uno',
])

/**
 * Busca las palabras de la consulta en el artículo. Una palabra en el título, resumen o categoría
 * vale 2 puntos y en los síntomas o pasos vale 1. Muestra primero los de más puntos y, a
 * igualdad, los más recientes.
 */
export function buscarArticulos(
  articulos: Articulo[],
  consulta: string,
  categoria: Categoria | 'todas',
) {
  const palabras = normalizar(consulta)
    .split(/\s+/)
    .filter((palabra) => palabra.length >= 3 && !PALABRAS_VACIAS.has(palabra))
  return articulos
    .filter((articulo) => categoria === 'todas' || articulo.categoria === categoria)
    .map((articulo) => {
      const principal = normalizar(
        [articulo.id, articulo.titulo, articulo.resumen, nombreCategoria(articulo.categoria)].join(
          ' ',
        ),
      )
      const resto = normalizar([...articulo.sintomas, ...articulo.pasos].join(' '))
      const puntos = palabras.reduce(
        (total, palabra) =>
          total + (principal.includes(palabra) ? 2 : resto.includes(palabra) ? 1 : 0),
        0,
      )
      return { articulo, puntos }
    })
    .filter(({ puntos }) => palabras.length === 0 || puntos > 0)
    .sort(
      (a, b) =>
        b.puntos - a.puntos || b.articulo.actualizado_en.localeCompare(a.articulo.actualizado_en),
    )
    .map(({ articulo }) => articulo)
}
