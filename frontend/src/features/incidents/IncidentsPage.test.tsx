import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { Impact, Incident, IncidentStatus, Urgency } from '@/api/incidents'
import { IncidentsPage } from './IncidentsPage'

// Backend falso con la forma de contracts/incidents/openapi.yaml y las transiciones de
// services/incidents/incidents/models.py. La página pasa por el cliente HTTP real.

const BASE = '/api/incidents/v1/incidents/'

const TRANSICIONES: Record<IncidentStatus, IncidentStatus[]> = {
  nuevo: ['asignado', 'rechazado', 'cancelado'],
  asignado: ['en_proceso', 'en_espera', 'rechazado', 'cancelado'],
  en_proceso: ['en_espera', 'resuelto', 'cancelado'],
  en_espera: ['en_proceso', 'cancelado'],
  resuelto: ['cerrado', 'reabierto'],
  reabierto: ['asignado', 'en_proceso'],
  cerrado: [],
  rechazado: [],
  cancelado: [],
}

const PESO = { alto: 0, medio: 1, bajo: 2, alta: 0, media: 1, baja: 2 }

function prioridad(impact: Impact, urgency: Urgency): Incident['priority'] {
  return (['P1', 'P2', 'P3', 'P4', 'P4'] as const)[PESO[impact] + PESO[urgency]]
}

/** Hora del 17-nov-2026 en ISO, para que coincida con el reloj fijo de las pruebas. */
function a(horas: number, minutos: number) {
  return new Date(2026, 10, 17, horas, minutos).toISOString()
}

function incidente(
  id: number,
  datos: Partial<Incident> & Pick<Incident, 'impact' | 'urgency' | 'created_at'>,
): Incident {
  return {
    id,
    code: `INC-${String(id).padStart(6, '0')}`,
    title: datos.description ?? 'Falla',
    reported_by: 'A-1000',
    status: 'nuevo',
    priority: prioridad(datos.impact, datos.urgency),
    assignment_group: 'nivel-1',
    updated_at: datos.created_at,
    ...datos,
  }
}

function json(datos: unknown, status = 200) {
  return new Response(JSON.stringify(datos), { status })
}

interface Llamada {
  method: string
  url: string
  body?: Record<string, unknown>
}

function servidorFalso(opciones: { fallar?: (llamada: Llamada) => Response | null } = {}) {
  const incidentes = new Map<number, Incident>(
    [
      incidente(49, {
        impact: 'alto',
        urgency: 'alta',
        created_at: a(11, 15),
        reported_by: 'A-1021',
        description: 'Sin acceso al sistema escolar',
      }),
      incidente(48, {
        impact: 'medio',
        urgency: 'media',
        created_at: a(11, 10),
        status: 'asignado',
        assigned_to: 'usr-002',
        assignment_group: 'nivel-2',
        updated_at: a(11, 30),
        description: 'Impresora del laboratorio no responde',
      }),
      incidente(47, {
        impact: 'bajo',
        urgency: 'baja',
        created_at: a(11, 2),
        status: 'cerrado',
        closed_at: a(11, 40),
        description: 'Solicitud de licencia de software',
      }),
      incidente(46, {
        impact: 'alto',
        urgency: 'alta',
        created_at: a(10, 55),
        status: 'en_proceso',
        assigned_to: 'usr-003',
        assignment_group: 'nivel-3',
        updated_at: a(11, 58),
        description: 'Servidor de base de datos caído',
      }),
      incidente(45, {
        impact: 'alto',
        urgency: 'media',
        created_at: a(10, 48),
        status: 'en_proceso',
        assigned_to: 'usr-002',
        assignment_group: 'nivel-2',
        updated_at: a(11, 45),
        description: 'Wi-Fi caído en el edificio B',
      }),
      incidente(44, {
        impact: 'medio',
        urgency: 'media',
        created_at: a(10, 30),
        status: 'cerrado',
        closed_at: a(11, 20),
        description: 'Correo institucional no envía mensajes',
      }),
    ].map((inc) => [inc.id, inc]),
  )
  const llamadas: Llamada[] = []

  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const llamada: Llamada = {
      method: init?.method ?? 'GET',
      url: String(input),
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    }
    llamadas.push(llamada)
    const fallo = opciones.fallar?.(llamada)
    if (fallo) return fallo

    if (llamada.method === 'GET' && llamada.url === BASE) {
      const results = [...incidentes.values()]
      return json({ count: results.length, next: null, previous: null, results })
    }
    if (llamada.method === 'POST' && llamada.url === BASE) {
      const body = llamada.body as Pick<Incident, 'impact' | 'urgency'> & Partial<Incident>
      const nuevo = incidente(50, { ...body, created_at: new Date().toISOString() })
      incidentes.set(50, nuevo)
      return json(nuevo, 201)
    }
    const id = Number(/\/incidents\/(\d+)\/$/.exec(llamada.url)?.[1])
    const actual = incidentes.get(id)
    if (llamada.method === 'PATCH' && actual) {
      const cambios = llamada.body as Partial<Incident>
      if (cambios.status && cambios.status !== actual.status) {
        if (!TRANSICIONES[actual.status ?? 'nuevo'].includes(cambios.status)) {
          return json(
            { status: [`No se puede pasar de «${actual.status}» a «${cambios.status}».`] },
            400,
          )
        }
        if (cambios.status === 'asignado' && !(cambios.assigned_to ?? actual.assigned_to)) {
          return json({ assigned_to: ['Para pasar a «asignado» hace falta un agente.'] }, 400)
        }
      }
      const ahora = new Date().toISOString()
      const actualizado: Incident = {
        ...actual,
        ...cambios,
        updated_at: ahora,
        ...(cambios.status === 'resuelto' && { resolved_at: ahora }),
        ...(cambios.status === 'cerrado' && { closed_at: ahora }),
      }
      incidentes.set(id, actualizado)
      return json(actualizado)
    }
    return json({ detail: 'No encontrado.' }, 404)
  })

  return { incidentes, llamadas }
}

// Reloj fijo a las 12:10 para que los datos coincidan con el diseño en Figma
// (INC-000049 a las 11:15, escalamientos «hace 12/25/40 min»). Solo se simula `Date`.
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 10, 17, 12, 10))
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

function row(ticketId: string) {
  const found = screen
    .getAllByRole('row')
    .find((element) => within(element).queryByText(ticketId) !== null)
  if (!found) throw new Error(`No hay fila para ${ticketId}`)
  return found
}

function metric(label: string) {
  return screen.getByText(label).parentElement!
}

/** Renderiza la página y espera a que la lista llegue del servicio. */
async function renderCargado(props: { agenteId?: string } = {}) {
  render(<IncidentsPage {...props} />)
  await screen.findByText('INC-000049')
}

async function openModal() {
  const user = userEvent.setup()
  await renderCargado()
  await user.click(screen.getByRole('button', { name: 'Nuevo ticket' }))
  return { user, dialog: screen.getByRole('dialog', { name: 'Abrir ticket' }) }
}

describe('IncidentsPage', () => {
  it('muestra los indicadores y los incidentes que devuelve el servicio', async () => {
    servidorFalso()
    await renderCargado()

    expect(within(metric('Tickets abiertos')).getByText('4')).toBeInTheDocument()
    expect(
      within(metric('Tickets abiertos')).getByText('1 nuevo en la última hora'),
    ).toBeInTheDocument()
    expect(within(metric('Tickets cerrados')).getByText('2')).toBeInTheDocument()
    expect(within(metric('Urgentes activos')).getByText('2')).toBeInTheDocument()
    expect(within(metric('Escalados')).getByText('3')).toBeInTheDocument()
    expect(within(metric('Escalados')).getByText('1 en Nivel 3')).toBeInTheDocument()
    expect(within(row('INC-000049')).getByText('11:15')).toBeInTheDocument()
    expect(screen.getByText('3 pendientes de llamada')).toBeInTheDocument()
    expect(screen.getByText(/al jefe de área · hace 12 min/)).toBeInTheDocument()
  })

  it('sin conexión muestra el error y se recupera al reintentar', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'))
    render(<IncidentsPage />)

    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('No se pudieron cargar los incidentes.')
    expect(alerta).toHaveTextContent('No hay conexión con el servicio')

    servidorFalso()
    await user.click(within(alerta).getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('INC-000049')).toBeInTheDocument()
  })

  it('escala un ticket: reasigna el grupo en el servicio y pide llamar a un supervisor', async () => {
    const user = userEvent.setup()
    const { llamadas } = servidorFalso()
    await renderCargado()

    await user.click(screen.getByRole('button', { name: 'Escalar INC-000049' }))

    await waitFor(() => expect(within(row('INC-000049')).getByText('Nivel 2')).toBeInTheDocument())
    expect(llamadas.at(-1)).toEqual({
      method: 'PATCH',
      url: `${BASE}49/`,
      body: { assignment_group: 'nivel-2' },
    })
    expect(screen.getByText('4 pendientes de llamada')).toBeInTheDocument()
    const aviso = screen.getByText('INC-000049 escalado a Nivel 2').closest('li')!
    expect(within(aviso).getByText(/llamar a un supervisor · hace un momento/)).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('INC-000049 escaló a Nivel 2')
  })

  it('si el servicio rechaza el escalamiento, lo avisa y no cambia el nivel', async () => {
    const user = userEvent.setup()
    servidorFalso({
      fallar: ({ method }) => (method === 'PATCH' ? json({}, 503) : null),
    })
    await renderCargado()

    await user.click(screen.getByRole('button', { name: 'Escalar INC-000049' }))

    expect(await screen.findByText(/No se pudo escalar INC-000049/)).toBeInTheDocument()
    expect(within(row('INC-000049')).getByText('Nivel 1')).toBeInTheDocument()
  })

  it('no deja escalar más allá del Nivel 3', async () => {
    servidorFalso()
    await renderCargado()

    expect(within(row('INC-000046')).getByRole('button', { name: 'Nivel máx.' })).toBeDisabled()
  })

  it('al cerrar un ticket lo resuelve y cierra en el servicio y retira sus avisos', async () => {
    const user = userEvent.setup()
    const { llamadas } = servidorFalso()
    await renderCargado()

    await user.click(screen.getByRole('button', { name: 'Cerrar INC-000046' }))

    await waitFor(() =>
      expect(within(row('INC-000046')).getByText('Ticket cerrado')).toBeInTheDocument(),
    )
    expect(llamadas.filter((l) => l.method === 'PATCH').map((l) => l.body?.status)).toEqual([
      'resuelto',
      'cerrado',
    ])
    expect(within(row('INC-000046')).getByText('Resuelto')).toBeInTheDocument()
    expect(screen.queryByText('INC-000046 escalado a Nivel 3')).not.toBeInTheDocument()
    expect(screen.getByText('2 pendientes de llamada')).toBeInTheDocument()
    expect(within(metric('Urgentes activos')).getByText('1')).toBeInTheDocument()
  })

  it('al cerrar un ticket nuevo lo asigna primero al agente de la sesión', async () => {
    const user = userEvent.setup()
    const { llamadas, incidentes } = servidorFalso()
    await renderCargado({ agenteId: 'usr-001' })

    await user.click(screen.getByRole('button', { name: 'Cerrar INC-000049' }))

    await waitFor(() => expect(incidentes.get(49)?.status).toBe('cerrado'))
    expect(llamadas.filter((l) => l.method === 'PATCH').map((l) => l.body)).toEqual([
      { status: 'asignado', assigned_to: 'usr-001' },
      { status: 'en_proceso' },
      { status: 'resuelto' },
      { status: 'cerrado' },
    ])
  })

  it('marca una llamada como realizada', async () => {
    const user = userEvent.setup()
    servidorFalso()
    await renderCargado()

    await user.click(
      screen.getByRole('button', { name: 'Marcar como llamado INC-000045 (Nivel 2)' }),
    )

    const aviso = screen.getByText('INC-000045 escalado a Nivel 2').closest('li')!
    expect(within(aviso).getByText('Llamada realizada')).toBeInTheDocument()
    expect(screen.getByText('2 pendientes de llamada')).toBeInTheDocument()
  })

  it('filtra la tabla por estado y prioridad', async () => {
    const user = userEvent.setup()
    servidorFalso()
    await renderCargado()

    await user.selectOptions(screen.getByLabelText('Filtrar por estado'), 'cerrado')
    expect(screen.getAllByRole('row')).toHaveLength(3) // encabezado + INC-000047 + INC-000044

    await user.selectOptions(screen.getByLabelText('Filtrar por prioridad'), 'baja')
    expect(screen.getAllByRole('row')).toHaveLength(2)
    expect(row('INC-000047')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Filtrar por prioridad'), 'urgente')
    expect(screen.getByText('No hay tickets con estos filtros.')).toBeInTheDocument()
  })

  it('abre el modal con el foco en el primer campo y valida los obligatorios', async () => {
    servidorFalso()
    const { user, dialog } = await openModal()
    const idField = within(dialog).getByLabelText(/id del solicitante/i)
    expect(idField).toHaveFocus()

    await user.click(within(dialog).getByRole('button', { name: 'Crear ticket' }))

    expect(within(dialog).getByText('Escribe el ID del solicitante.')).toBeInTheDocument()
    expect(within(dialog).getByText('Escribe el nombre del solicitante.')).toBeInTheDocument()
    expect(within(dialog).getByText('Describe la falla.')).toBeInTheDocument()
    expect(idField).toHaveFocus()
  })

  it('crea el incidente en el servicio y lo agrega al inicio de la tabla', async () => {
    const { llamadas } = servidorFalso()
    const { user, dialog } = await openModal()

    await user.type(within(dialog).getByLabelText(/id del solicitante/i), 'a-1077')
    await user.type(within(dialog).getByLabelText(/nombre del solicitante/i), 'Elena Soto')
    await user.click(within(dialog).getByRole('radio', { name: 'Teléfono' }))
    await user.type(
      within(dialog).getByLabelText(/descripción breve/i),
      'El proyector del aula 3 no enciende desde la mañana.',
    )
    await user.selectOptions(within(dialog).getByLabelText('Urgencia'), 'alta')
    await user.upload(
      within(dialog).getByLabelText(/evidencia/i),
      new File(['foto'], 'proyector.png', { type: 'image/png' }),
    )
    expect(within(dialog).getByText('proyector.png')).toBeInTheDocument()
    await user.click(within(dialog).getByRole('button', { name: 'Crear ticket' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(llamadas.find((l) => l.method === 'POST')).toEqual({
      method: 'POST',
      url: BASE,
      body: {
        title: 'El proyector del aula 3 no enciende desde la mañana.',
        description: 'El proyector del aula 3 no enciende desde la mañana.',
        impact: 'medio',
        urgency: 'alta',
        reported_by: 'A-1077',
        assignment_group: 'nivel-1',
      },
    })
    expect(screen.getByRole('status')).toHaveTextContent('Ticket INC-000050 creado')
    const nuevo = row('INC-000050')
    expect(within(nuevo).getByText('Elena Soto')).toBeInTheDocument()
    expect(within(nuevo).getByText('A-1077')).toBeInTheDocument()
    expect(within(nuevo).getByText('Teléfono')).toBeInTheDocument()
    expect(within(nuevo).getByText('Evidencia adjunta')).toBeInTheDocument()
    expect(within(metric('Tickets abiertos')).getByText('5')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nuevo ticket' })).toHaveFocus()
  })

  it('si el servicio rechaza el alta, conserva el formulario y muestra el motivo', async () => {
    servidorFalso({
      fallar: ({ method }) =>
        method === 'POST' ? json({ reported_by: ['Este campo no es válido.'] }, 400) : null,
    })
    const { user, dialog } = await openModal()

    await user.type(within(dialog).getByLabelText(/id del solicitante/i), 'a-1077')
    await user.type(within(dialog).getByLabelText(/nombre del solicitante/i), 'Elena Soto')
    await user.type(
      within(dialog).getByLabelText(/descripción breve/i),
      'El proyector del aula 3 no enciende desde la mañana.',
    )
    await user.click(within(dialog).getByRole('button', { name: 'Crear ticket' }))

    expect(await within(dialog).findByRole('alert')).toHaveTextContent(
      'No se pudo registrar el incidente: Este campo no es válido.',
    )
    expect(within(dialog).getByLabelText(/nombre del solicitante/i)).toHaveValue('Elena Soto')
    expect(within(dialog).getByRole('button', { name: 'Crear ticket' })).toBeEnabled()
  })

  it('rechaza evidencia de más de 10 MB', async () => {
    servidorFalso()
    const { user, dialog } = await openModal()
    const grande = new File(['x'], 'video.png', { type: 'image/png' })
    Object.defineProperty(grande, 'size', { value: 11 * 1024 * 1024 })

    await user.upload(within(dialog).getByLabelText(/evidencia/i), grande)

    expect(
      within(dialog).getByText('El archivo pesa más de 10 MB. Elige uno más ligero.'),
    ).toBeInTheDocument()
    expect(within(dialog).queryByText('video.png')).not.toBeInTheDocument()
  })

  it('se cierra con Escape y devuelve el foco al botón «Nuevo ticket»', async () => {
    servidorFalso()
    const { user } = await openModal()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nuevo ticket' })).toHaveFocus()
  })
})
