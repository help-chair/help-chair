import type { Articulo, Categoria } from './types'

// Catálogos, artículos de ejemplo (mocks) y utilidades del módulo mientras services/knowledge
// publica su API. Los artículos son los del diseño (frontend/docs/knowledge/).

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

/** Artículos de ejemplo frescos (cada llamada devuelve copias nuevas). */
export function crearArticulosDeEjemplo(): Articulo[] {
  return [
    {
      id: 'KB-028',
      titulo: 'Cómo conectarte a la red de respaldo del edificio B',
      resumen:
        'Si el Wi-Fi del edificio B se cae, usa la red CETI-B-2 mientras se instala el nuevo punto de acceso.',
      categoria: 'red',
      visibilidad: 'publico',
      error_conocido_id: 6,
      sintomas: [
        'Tu equipo se desconecta de la red CETI-B dentro del edificio B.',
        'La red aparece conectada, pero ninguna página abre.',
        'Pasa sobre todo entre las 10:00 y las 13:00.',
      ],
      pasos: [
        'Abre la configuración de Wi-Fi de tu equipo y desconéctate de CETI-B.',
        'En la lista de redes elige CETI-B-2. Si no aparece, acércate a la planta baja, donde está el punto de acceso AP-B2.',
        'Inicia sesión con tu correo institucional y tu contraseña de siempre.',
        'Si tu equipo pregunta por un certificado, elige «Confiar».',
        'Abre el sistema escolar para confirmar que ya tienes internet.',
      ],
      si_no_funciona:
        'Registra una incidencia con tu salón y la hora en que perdiste la conexión. Así el equipo de Problemas suma tu caso al análisis.',
      autor: 'Marco Estrada',
      actualizado_en: '2026-11-12T17:00:00Z',
      consultas: 312,
      votos_utiles: 113,
      votos_no_utiles: 7,
    },
    {
      id: 'KB-031',
      titulo: 'Liberar espacio en bd-cluster-02 con el script de limpieza',
      resumen:
        'Pasos para borrar logs antiguos y reiniciar la réplica cuando el disco pasa de 85 %.',
      categoria: 'base_datos',
      visibilidad: 'agentes',
      error_conocido_id: 7,
      sintomas: [
        'El monitor de eventos marca «Espacio en disco > 85 %» en bd-cluster-02.',
        'El servidor de base de datos responde lento o deja de responder.',
      ],
      pasos: [
        'Entra al nodo bd-cluster-02 con tu usuario de operaciones.',
        'Ejecuta el script de limpieza de logs de réplica que está en la carpeta de mantenimiento.',
        'Reinicia el servicio de réplica.',
        'Confirma en el monitor de eventos que el uso del disco bajó.',
      ],
      si_no_funciona:
        'Escala la incidencia a Nivel 2 y vincúlala al problema PRB-014 para que se tome en cuenta en el análisis.',
      autor: 'Daniela Ruiz',
      actualizado_en: '2026-11-11T19:30:00Z',
      consultas: 41,
      votos_utiles: 22,
      votos_no_utiles: 3,
    },
    {
      id: 'KB-025',
      titulo: 'Restablecer tu contraseña del sistema escolar',
      resumen: 'Recupera el acceso con tu correo institucional en menos de 5 minutos.',
      categoria: 'accesos',
      visibilidad: 'publico',
      error_conocido_id: null,
      sintomas: [
        'El sistema escolar dice que tu contraseña es incorrecta.',
        'Tu cuenta se bloqueó después de varios intentos.',
      ],
      pasos: [
        'En la pantalla de inicio de sesión elige «¿Olvidaste tu contraseña?».',
        'Escribe tu correo institucional.',
        'Abre el enlace que llega a tu correo; dura 30 minutos.',
        'Escribe tu contraseña nueva dos veces y guárdala.',
      ],
      si_no_funciona:
        'Si el correo no llega en 10 minutos, revisa la carpeta de spam o registra una petición de acceso.',
      autor: 'Sofía Marín',
      actualizado_en: '2026-11-08T16:00:00Z',
      consultas: 540,
      votos_utiles: 128,
      votos_no_utiles: 12,
    },
    {
      id: 'KB-022',
      titulo: 'Enviar archivos de más de 10 MB por correo institucional',
      resumen:
        'Comparte archivos grandes con un enlace de tu nube institucional en lugar de adjuntarlos.',
      categoria: 'correo',
      visibilidad: 'publico',
      error_conocido_id: null,
      sintomas: [
        'El correo rebota cuando adjuntas un archivo grande.',
        'El mensaje se queda en la bandeja de salida.',
      ],
      pasos: [
        'Sube el archivo a tu nube institucional.',
        'Copia el enlace para compartir y da permiso de lectura a los destinatarios.',
        'Pega el enlace en el correo en lugar de adjuntar el archivo.',
      ],
      si_no_funciona: 'Registra una incidencia con el tamaño del archivo y la hora del envío.',
      autor: 'Daniela Ruiz',
      actualizado_en: '2026-11-05T15:20:00Z',
      consultas: 198,
      votos_utiles: 38,
      votos_no_utiles: 12,
    },
    {
      id: 'KB-019',
      titulo: 'Agregar la impresora del laboratorio en Windows y macOS',
      resumen: 'Configura la impresora LAB-B4 con su dirección IP fija en pocos pasos.',
      categoria: 'impresoras',
      visibilidad: 'publico',
      error_conocido_id: null,
      sintomas: ['La impresora del laboratorio no aparece en tu equipo.'],
      pasos: [
        'Abre la configuración de impresoras de tu sistema.',
        'Elige «Agregar impresora» y luego «Por dirección IP».',
        'Escribe la dirección que aparece en la etiqueta de la impresora LAB-B4.',
        'Imprime una página de prueba.',
      ],
      si_no_funciona:
        'Si después de una actualización de Windows dejó de imprimir, registra una incidencia: hay un problema abierto sobre eso.',
      autor: 'Marco Estrada',
      actualizado_en: '2026-11-02T18:10:00Z',
      consultas: 156,
      votos_utiles: 44,
      votos_no_utiles: 9,
    },
    {
      id: 'KB-014',
      titulo: 'Instalar el cliente VPN para trabajo remoto',
      resumen: 'Conéctate a los sistemas internos desde casa con la VPN institucional.',
      categoria: 'software',
      visibilidad: 'publico',
      error_conocido_id: null,
      sintomas: ['No puedes abrir los sistemas internos fuera de la escuela.'],
      pasos: [
        'Descarga el cliente VPN desde el portal de autoservicio.',
        'Instálalo y ábrelo.',
        'Inicia sesión con tu correo institucional.',
      ],
      si_no_funciona: 'Registra una petición de acceso a la VPN desde el catálogo de servicios.',
      autor: 'Sofía Marín',
      actualizado_en: '2026-10-28T17:00:00Z',
      consultas: 227,
      votos_utiles: 67,
      votos_no_utiles: 8,
    },
  ]
}

/**
 * Simula la respuesta de services/knowledge. Cuando exista la API, se reemplaza por las
 * llamadas en src/api/ y la pantalla no cambia.
 */
export function cargarArticulosDeEjemplo(): Promise<Articulo[]> {
  return new Promise((resolve) => setTimeout(() => resolve(crearArticulosDeEjemplo()), 300))
}
