import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProblemsPage } from './ProblemsPage'
import type {
  CambioEstado,
  DatosProblemas,
  ErrorConocido,
  ErrorConocidoCrear,
  Problema,
  ProblemaCrear,
  ProblemaIncidente,
} from './types'

// Fixture de prueba: los casos del diseño, con la forma de contracts/problems/openapi.yaml.

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

/** Casos del diseño (frontend/docs/problems/), frescos en cada llamada. */
function crearDatosDeEjemplo(): DatosProblemas {
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

// Carga inmediata con el fixture (la lectura desde la API se prueba en src/api/problems.test.ts).
const cargarAlInstante = () => Promise.resolve(crearDatosDeEjemplo())

const BASE = '/api/problems/v1'

function json(datos: unknown, status = 200) {
  return new Response(JSON.stringify(datos), { status })
}

interface Llamada {
  method: string
  url: string
  body?: unknown
}

const RUTA_ESTADO = /^\/api\/problems\/v1\/problemas\/(\d+)\/estado\/$/
const RUTA_VINCULOS = /^\/api\/problems\/v1\/problemas\/(\d+)\/incidentes\/$/

/** services/problems falso para las escrituras: responde como el contrato. */
function servicioFalso(opciones: { fallar?: (llamada: Llamada) => Response | null } = {}) {
  const { problemas, errores } = crearDatosDeEjemplo()
  const porId = new Map(problemas.map((problema) => [problema.id, problema]))
  const llamadas: Llamada[] = []
  const ahora = () => new Date().toISOString()

  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const llamada: Llamada = {
      method: init?.method ?? 'GET',
      url: String(input),
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    }
    llamadas.push(llamada)
    const fallo = opciones.fallar?.(llamada)
    if (fallo) return fallo

    if (llamada.method === 'POST' && llamada.url === `${BASE}/problemas/`) {
      const entrada = llamada.body as ProblemaCrear
      const nuevo: Problema = {
        id: Math.max(...porId.keys()) + 1,
        titulo: entrada.titulo,
        descripcion: entrada.descripcion,
        estado: 'registrado',
        prioridad: entrada.prioridad ?? 'media',
        origen: entrada.origen ?? 'manual',
        causa_raiz: entrada.causa_raiz ?? '',
        asignado_a_id: entrada.asignado_a_id ?? '',
        creado_en: ahora(),
        actualizado_en: ahora(),
        resuelto_en: null,
      }
      porId.set(nuevo.id, nuevo)
      return json(nuevo, 201)
    }
    const estado = RUTA_ESTADO.exec(llamada.url)
    if (llamada.method === 'POST' && estado) {
      const cambio = llamada.body as CambioEstado
      const actual = porId.get(Number(estado[1]))!
      const actualizado: Problema = {
        ...actual,
        estado: cambio.estado,
        causa_raiz: cambio.causa_raiz ?? actual.causa_raiz,
        actualizado_en: ahora(),
      }
      porId.set(actualizado.id, actualizado)
      return json(actualizado)
    }
    const vinculo = RUTA_VINCULOS.exec(llamada.url)
    if (llamada.method === 'POST' && vinculo) {
      const { incidente_id } = llamada.body as { incidente_id: string }
      const nuevo: ProblemaIncidente = {
        id: 999,
        problema_id: Number(vinculo[1]),
        incidente_id,
        vinculado_en: ahora(),
      }
      return json(nuevo, 201)
    }
    if (llamada.method === 'DELETE') return new Response(null, { status: 204 })
    if (llamada.method === 'POST' && llamada.url === `${BASE}/errores-conocidos/`) {
      const entrada = llamada.body as ErrorConocidoCrear
      const nuevo: ErrorConocido = {
        ...entrada,
        id: Math.max(...errores.map((error) => error.id)) + 1,
        articulo_kb_id: entrada.articulo_kb_id ?? '',
        activo: true,
        creado_en: ahora(),
        actualizado_en: ahora(),
      }
      return json(nuevo, 201)
    }
    return json({ codigo: 'no_encontrado', detalle: 'No encontrado.' }, 404)
  })

  return { llamadas }
}

afterEach(() => {
  vi.restoreAllMocks()
})

async function renderPage() {
  const user = userEvent.setup()
  render(<ProblemsPage cargarDatos={cargarAlInstante} />)
  await screen.findByRole('table', { name: 'Problemas registrados' })
  return user
}

function fila(codigo: string) {
  const encontrada = screen
    .getAllByRole('row')
    .find((element) => within(element).queryByText(codigo) !== null)
  if (!encontrada) throw new Error(`No hay fila para ${codigo}`)
  return encontrada
}

function indicador(label: string) {
  return screen.getByText(label).parentElement!
}

async function abrirDetalle(user: ReturnType<typeof userEvent.setup>, codigo: string) {
  await user.click(screen.getByRole('button', { name: `Ver análisis de ${codigo}` }))
}

async function avisoDice(texto: string) {
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(texto))
}

describe('ProblemsPage', () => {
  it('muestra los indicadores, la tabla y los errores conocidos del diseño', async () => {
    await renderPage()

    expect(within(indicador('Problemas abiertos')).getByText('5')).toBeInTheDocument()
    expect(
      within(indicador('Problemas abiertos')).getByText('2 con prioridad crítica'),
    ).toBeInTheDocument()
    expect(within(indicador('Detectados por patrón')).getByText('4')).toBeInTheDocument()
    expect(within(indicador('Errores conocidos')).getByText('2')).toBeInTheDocument()
    expect(within(indicador('Incidencias vinculadas')).getByText('34')).toBeInTheDocument()
    expect(within(fila('PRB-015')).getByText('Error conocido')).toBeInTheDocument()
    expect(within(fila('PRB-015')).getByText('7')).toBeInTheDocument()
    expect(screen.getByText('2 activos · 1 retirado')).toBeInTheDocument()
  })

  it('filtra por estado y prioridad, y ofrece quitar los filtros', async () => {
    const user = await renderPage()

    await user.selectOptions(screen.getByLabelText('Filtrar por estado'), 'resuelto')
    expect(screen.getByText('PRB-011')).toBeInTheDocument()
    expect(screen.queryByText('PRB-015')).not.toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Filtrar por prioridad'), 'critica')
    expect(screen.getByText('Ningún problema coincide con esos filtros')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Quitar filtros' }))
    expect(screen.getByText('PRB-015')).toBeInTheDocument()
  })

  it('abre el detalle con los 5 porqués, la causa raíz y el error conocido', async () => {
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-015')

    expect(
      screen.getByRole('heading', { name: 'Caídas recurrentes del Wi-Fi en el edificio B' }),
    ).toBeInTheDocument()
    expect(screen.getByText('¿Por qué se reinicia solo?')).toBeInTheDocument()
    expect(
      screen.getByText(/un solo punto de acceso para más de 80 dispositivos/),
    ).toBeInTheDocument()
    expect(screen.getByText('KE-006')).toBeInTheDocument()
    const tabla = screen.getByRole('table', { name: 'Incidencias vinculadas a PRB-015' })
    expect(within(tabla).getAllByRole('row')).toHaveLength(8) // encabezado + 7 incidencias

    await user.click(screen.getByRole('button', { name: 'Volver a Problemas' }))
    expect(screen.getByRole('table', { name: 'Problemas registrados' })).toBeInTheDocument()
  })

  it('registra un problema en el servicio y valida los campos obligatorios', async () => {
    const { llamadas } = servicioFalso()
    const user = await renderPage()

    await user.click(screen.getByRole('button', { name: 'Registrar problema' }))
    const dialogo = screen.getByRole('dialog', { name: 'Registrar problema' })
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar problema' }))
    expect(within(dialogo).getByText('Escribe un título para el problema.')).toBeInTheDocument()
    expect(within(dialogo).getByLabelText(/Título/)).toHaveFocus()
    expect(llamadas).toHaveLength(0)

    await user.type(
      within(dialogo).getByLabelText(/Título/),
      'Proyectores del edificio C sin señal',
    )
    await user.type(
      within(dialogo).getByLabelText(/Descripción/),
      'Fallan cada lunes por la mañana.',
    )
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar problema' }))

    await avisoDice('Problema PRB-017 registrado')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(llamadas[0]).toMatchObject({
      method: 'POST',
      url: `${BASE}/problemas/`,
      body: { titulo: 'Proyectores del edificio C sin señal', origen: 'manual' },
    })
    expect(within(fila('PRB-017')).getByText('Registrado')).toBeInTheDocument()
    expect(within(indicador('Problemas abiertos')).getByText('6')).toBeInTheDocument()
  })

  it('si el servicio rechaza el registro, el modal sigue abierto con el motivo', async () => {
    servicioFalso({
      fallar: () =>
        json({ codigo: 'datos_invalidos', detalle: 'El título ya existe en otro problema.' }, 400),
    })
    const user = await renderPage()

    await user.click(screen.getByRole('button', { name: 'Registrar problema' }))
    const dialogo = screen.getByRole('dialog', { name: 'Registrar problema' })
    await user.type(within(dialogo).getByLabelText(/Título/), 'Wi-Fi caído')
    await user.type(within(dialogo).getByLabelText(/Descripción/), 'Otra vez.')
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar problema' }))

    expect(await within(dialogo).findByRole('alert')).toHaveTextContent(
      'El título ya existe en otro problema.',
    )
    expect(within(dialogo).getByLabelText(/Título/)).toHaveValue('Wi-Fi caído')
  })

  it('pide la causa raíz antes de pasar a «Causa identificada»', async () => {
    const { llamadas } = servicioFalso()
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-016')

    await user.click(screen.getByRole('button', { name: 'Registrar causa raíz' }))
    const dialogo = screen.getByRole('dialog', { name: 'Registrar causa raíz' })
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar causa raíz' }))
    expect(within(dialogo).getByText('Escribe la causa raíz para continuar.')).toBeInTheDocument()

    await user.type(
      within(dialogo).getByLabelText(/Causa raíz/),
      'El servidor de correo limita los adjuntos a 10 MB.',
    )
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar causa raíz' }))

    await avisoDice('Causa raíz registrada en PRB-016.')
    expect(llamadas.at(-1)).toEqual({
      method: 'POST',
      url: `${BASE}/problemas/16/estado/`,
      body: {
        estado: 'causa_identificada',
        causa_raiz: 'El servidor de correo limita los adjuntos a 10 MB.',
      },
    })
    expect(
      screen.getByText('El servidor de correo limita los adjuntos a 10 MB.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Publicar error conocido' })).toBeInTheDocument()
  })

  it('publica un error conocido con su solución temporal', async () => {
    servicioFalso()
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-012')

    await user.click(screen.getByRole('button', { name: 'Publicar error conocido' }))
    const dialogo = screen.getByRole('dialog', { name: 'Publicar error conocido' })
    await user.type(
      within(dialogo).getByLabelText(/Solución temporal/),
      'Reintentar el cobro después de 30 segundos.',
    )
    await user.click(within(dialogo).getByRole('button', { name: 'Publicar error conocido' }))

    await avisoDice('Error conocido KE-008 publicado para PRB-012.')
    expect(screen.getByText('Reintentar el cobro después de 30 segundos.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Marcar como resuelto' })).toBeInTheDocument()
  })

  it('vincula y desvincula incidencias, sin repetir la misma', async () => {
    const { llamadas } = servicioFalso()
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-015')

    await user.click(screen.getByRole('button', { name: 'Vincular incidencia' }))
    const dialogo = screen.getByRole('dialog', { name: 'Vincular incidencia' })
    const campo = within(dialogo).getByLabelText(/ID de la incidencia/)
    await user.type(campo, 'tck-1045')
    await user.click(within(dialogo).getByRole('button', { name: 'Vincular incidencia' }))
    expect(
      await within(dialogo).findByText('TCK-1045 ya está vinculada a PRB-015.'),
    ).toBeInTheDocument()

    await user.clear(campo)
    await user.type(campo, 'INC-000050')
    await user.click(within(dialogo).getByRole('button', { name: 'Vincular incidencia' }))
    await avisoDice('Incidencia INC-000050 vinculada a PRB-015.')
    expect(screen.getByText('INC-000050')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Desvincular INC-000050' }))
    await avisoDice('Incidencia INC-000050 desvinculada de PRB-015.')
    expect(screen.queryByText('INC-000050')).not.toBeInTheDocument()
    expect(llamadas.at(-1)).toEqual({
      method: 'DELETE',
      url: `${BASE}/problemas/15/incidentes/INC-000050/`,
      body: undefined,
    })
  })

  it('muestra el 409 del servicio si la incidencia ya estaba vinculada', async () => {
    servicioFalso({
      fallar: ({ method }) =>
        method === 'POST'
          ? json(
              { codigo: 'incidente_ya_vinculado', detalle: 'INC-1 ya está vinculado a PRB-15.' },
              409,
            )
          : null,
    })
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-015')

    await user.click(screen.getByRole('button', { name: 'Vincular incidencia' }))
    const dialogo = screen.getByRole('dialog', { name: 'Vincular incidencia' })
    await user.type(within(dialogo).getByLabelText(/ID de la incidencia/), 'INC-1')
    await user.click(within(dialogo).getByRole('button', { name: 'Vincular incidencia' }))

    expect(
      await within(dialogo).findByText('INC-1 ya está vinculado a PRB-15.'),
    ).toBeInTheDocument()
  })

  it('muestra un error con reintento si el servicio no responde', async () => {
    const user = userEvent.setup()
    const cargar = vi
      .fn()
      .mockRejectedValueOnce(new Error('sin conexión'))
      .mockImplementation(cargarAlInstante)
    render(<ProblemsPage cargarDatos={cargar} />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudieron cargar los problemas.',
    )
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('table', { name: 'Problemas registrados' })).toBeInTheDocument()
  })
})
