import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { KnowledgePage } from './KnowledgePage'
import type { Articulo } from './types'

// Fixture de prueba: los artículos del diseño. La lectura desde la API se prueba en api.test.ts.

/** Artículos del diseño (frontend/docs/knowledge/), frescos en cada llamada. */
function crearArticulosDeEjemplo(): Articulo[] {
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

// Carga inmediata con el fixture.
const cargarAlInstante = () => Promise.resolve(crearArticulosDeEjemplo())

async function renderPage() {
  const user = userEvent.setup()
  render(<KnowledgePage cargarArticulos={cargarAlInstante} />)
  await screen.findByRole('heading', { name: 'Artículos recientes' })
  return user
}

async function buscar(user: ReturnType<typeof userEvent.setup>, texto: string) {
  const buscador = screen.getByRole('searchbox', { name: 'Buscar en la Base de Conocimiento' })
  await user.clear(buscador)
  await user.type(buscador, texto)
  await user.click(screen.getByRole('button', { name: 'Buscar solución' }))
}

describe('KnowledgePage', () => {
  it('lista los artículos, los más útiles y los que necesitan mejora', async () => {
    await renderPage()

    expect(
      screen.getAllByRole('button', {
        name: 'Cómo conectarte a la red de respaldo del edificio B',
      }),
    ).not.toHaveLength(0)
    expect(screen.getByText('Solución temporal · KE-006')).toBeInTheDocument()
    expect(
      screen.getByRole('button', {
        name: 'KB-022 · Enviar archivos de más de 10 MB por correo institucional',
      }),
    ).toBeInTheDocument()
    expect(screen.getByText('12 personas dijeron que no les sirvió')).toBeInTheDocument()
  })

  it('encuentra artículos aunque se escriba sin acentos ni guiones', async () => {
    const user = await renderPage()

    await buscar(user, 'no tengo wifi en el edificio B')
    const resultados = screen.getByRole('region', { name: /para «no tengo wifi en el edificio B»/ })
    expect(
      within(resultados).getByRole('heading', { level: 4, name: /^1 resultado/ }),
    ).toBeInTheDocument()
    expect(
      within(resultados).getByRole('button', {
        name: 'Cómo conectarte a la red de respaldo del edificio B',
      }),
    ).toBeInTheDocument()

    // KB-028 también la menciona en un paso, pero va primero la que la tiene en el título.
    await buscar(user, 'contrasena')
    const porContrasena = screen.getByRole('region', { name: '2 resultados para «contrasena»' })
    expect(within(porContrasena).getAllByRole('listitem')[0]).toHaveTextContent(
      'Restablecer tu contraseña del sistema escolar',
    )
  })

  it('filtra por etiqueta y ofrece limpiar la búsqueda cuando no hay resultados', async () => {
    const user = await renderPage()

    await user.click(screen.getByRole('button', { name: 'Impresoras · 1' }))
    expect(screen.getByRole('button', { name: 'Impresoras · 1' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await buscar(user, 'vpn')
    expect(screen.getByText('No encontramos artículos para «vpn»')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Limpiar búsqueda' }))
    expect(screen.getByRole('heading', { name: 'Artículos recientes' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Todas · 6' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('abre un artículo y registra que sí sirvió', async () => {
    const user = await renderPage()

    await user.click(
      screen.getAllByRole('button', {
        name: 'Cómo conectarte a la red de respaldo del edificio B',
      })[0],
    )
    expect(
      screen.getByRole('heading', { name: 'Cómo conectarte a la red de respaldo del edificio B' }),
    ).toBeInTheDocument()
    expect(screen.getByText('113 de 120 personas dijeron que sí.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Sí, me sirvió' }))
    expect(screen.getByRole('status')).toHaveTextContent('Gracias, registramos tu respuesta.')

    await user.click(screen.getByRole('button', { name: 'Volver a la Base de Conocimiento' }))
    expect(screen.getByRole('heading', { name: 'Artículos recientes' })).toBeInTheDocument()
  })

  it('si no sirvió, pide qué le faltó antes de registrar la respuesta', async () => {
    const user = await renderPage()

    await user.click(
      screen.getAllByRole('button', {
        name: 'Cómo conectarte a la red de respaldo del edificio B',
      })[0],
    )
    await user.click(screen.getByRole('button', { name: 'No me sirvió' }))
    await user.type(
      screen.getByLabelText('¿Qué le faltó al artículo?'),
      'La red CETI-B-2 no aparece en el segundo piso.',
    )
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))
    expect(screen.getByRole('status')).toHaveTextContent('Gracias, registramos tu respuesta.')

    // 113 de 121 votos: el porcentaje baja de 94 % a 93 %.
    await user.click(screen.getByRole('button', { name: 'Volver a la Base de Conocimiento' }))
    expect(screen.getAllByText('93 % útil').length).toBeGreaterThan(0)
  })

  it('muestra un error con reintento si el servicio no responde', async () => {
    const user = userEvent.setup()
    const cargar = vi
      .fn()
      .mockRejectedValueOnce(new Error('sin conexión'))
      .mockImplementation(cargarAlInstante)
    render(<KnowledgePage cargarArticulos={cargar} />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudieron cargar los artículos.',
    )
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('heading', { name: 'Artículos recientes' })).toBeInTheDocument()
  })
})
