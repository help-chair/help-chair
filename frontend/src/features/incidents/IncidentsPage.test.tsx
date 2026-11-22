import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { IncidentsPage } from './IncidentsPage'

// Reloj fijo a las 12:10 para que los datos de ejemplo coincidan con el diseño en Figma
// (TCK-1049 a las 11:15, escalamientos «hace 12/25/40 min»). Solo se simula `Date`.
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 10, 17, 12, 10))
})

afterEach(() => {
  vi.useRealTimers()
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

async function openModal() {
  const user = userEvent.setup()
  render(<IncidentsPage />)
  await user.click(screen.getByRole('button', { name: 'Nuevo ticket' }))
  return { user, dialog: screen.getByRole('dialog', { name: 'Abrir ticket' }) }
}

describe('IncidentsPage', () => {
  it('muestra los indicadores y los casos del diseño', () => {
    render(<IncidentsPage />)

    expect(within(metric('Tickets abiertos')).getByText('4')).toBeInTheDocument()
    expect(
      within(metric('Tickets abiertos')).getByText('1 nuevo en la última hora'),
    ).toBeInTheDocument()
    expect(within(metric('Tickets cerrados')).getByText('2')).toBeInTheDocument()
    expect(within(metric('Urgentes activos')).getByText('2')).toBeInTheDocument()
    expect(within(metric('Escalados')).getByText('3')).toBeInTheDocument()
    expect(within(metric('Escalados')).getByText('1 en Nivel 3')).toBeInTheDocument()
    expect(within(row('TCK-1049')).getByText('11:15')).toBeInTheDocument()
    expect(screen.getByText('3 pendientes de llamada')).toBeInTheDocument()
    expect(screen.getByText(/al jefe de área · hace 12 min/)).toBeInTheDocument()
  })

  it('escala un ticket: sube de nivel y pide llamar a un supervisor', async () => {
    const user = userEvent.setup()
    render(<IncidentsPage />)

    await user.click(screen.getByRole('button', { name: 'Escalar TCK-1049' }))

    expect(within(row('TCK-1049')).getByText('Nivel 2')).toBeInTheDocument()
    expect(screen.getByText('4 pendientes de llamada')).toBeInTheDocument()
    const aviso = screen.getByText('TCK-1049 escalado a Nivel 2').closest('li')!
    expect(within(aviso).getByText(/llamar a un supervisor · hace un momento/)).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('TCK-1049 escaló a Nivel 2')
  })

  it('no deja escalar más allá del Nivel 3', () => {
    render(<IncidentsPage />)

    expect(within(row('TCK-1046')).getByRole('button', { name: 'Nivel máx.' })).toBeDisabled()
  })

  it('al cerrar un ticket lo marca como resuelto y retira sus avisos pendientes', async () => {
    const user = userEvent.setup()
    render(<IncidentsPage />)

    await user.click(screen.getByRole('button', { name: 'Cerrar TCK-1046' }))

    expect(within(row('TCK-1046')).getByText('Ticket cerrado')).toBeInTheDocument()
    expect(within(row('TCK-1046')).getByText('Resuelto')).toBeInTheDocument()
    expect(screen.queryByText('TCK-1046 escalado a Nivel 3')).not.toBeInTheDocument()
    expect(screen.getByText('2 pendientes de llamada')).toBeInTheDocument()
    expect(within(metric('Urgentes activos')).getByText('1')).toBeInTheDocument()
  })

  it('marca una llamada como realizada', async () => {
    const user = userEvent.setup()
    render(<IncidentsPage />)

    await user.click(screen.getByRole('button', { name: 'Marcar como llamado TCK-1045 (Nivel 2)' }))

    const aviso = screen.getByText('TCK-1045 escalado a Nivel 2').closest('li')!
    expect(within(aviso).getByText('Llamada realizada')).toBeInTheDocument()
    expect(screen.getByText('2 pendientes de llamada')).toBeInTheDocument()
  })

  it('filtra la tabla por estado y prioridad', async () => {
    const user = userEvent.setup()
    render(<IncidentsPage />)

    await user.selectOptions(screen.getByLabelText('Filtrar por estado'), 'cerrado')
    expect(screen.getAllByRole('row')).toHaveLength(3) // encabezado + TCK-1047 + TCK-1044

    await user.selectOptions(screen.getByLabelText('Filtrar por prioridad'), 'baja')
    expect(screen.getAllByRole('row')).toHaveLength(2)
    expect(row('TCK-1047')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Filtrar por prioridad'), 'urgente')
    expect(screen.getByText('No hay tickets con estos filtros.')).toBeInTheDocument()
  })

  it('abre el modal con el foco en el primer campo y valida los obligatorios', async () => {
    const { user, dialog } = await openModal()
    const idField = within(dialog).getByLabelText(/id del solicitante/i)
    expect(idField).toHaveFocus()

    await user.click(within(dialog).getByRole('button', { name: 'Crear ticket' }))

    expect(within(dialog).getByText('Escribe el ID del solicitante.')).toBeInTheDocument()
    expect(within(dialog).getByText('Escribe el nombre del solicitante.')).toBeInTheDocument()
    expect(within(dialog).getByText('Describe la falla.')).toBeInTheDocument()
    expect(idField).toHaveFocus()
  })

  it('crea un ticket con evidencia y lo agrega al inicio de la tabla', async () => {
    const { user, dialog } = await openModal()

    await user.type(within(dialog).getByLabelText(/id del solicitante/i), 'a-1077')
    await user.type(within(dialog).getByLabelText(/nombre del solicitante/i), 'Elena Soto')
    await user.click(within(dialog).getByRole('radio', { name: 'Teléfono' }))
    await user.type(
      within(dialog).getByLabelText(/descripción breve/i),
      'El proyector del aula 3 no enciende desde la mañana.',
    )
    await user.selectOptions(within(dialog).getByLabelText('Urgencia'), 'alta')
    await user.selectOptions(within(dialog).getByLabelText('Prioridad'), 'urgente')
    await user.upload(
      within(dialog).getByLabelText(/evidencia/i),
      new File(['foto'], 'proyector.png', { type: 'image/png' }),
    )
    expect(within(dialog).getByText('proyector.png')).toBeInTheDocument()
    await user.click(within(dialog).getByRole('button', { name: 'Crear ticket' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Ticket TCK-1050 creado')
    const nuevo = row('TCK-1050')
    expect(within(nuevo).getByText('Elena Soto')).toBeInTheDocument()
    expect(within(nuevo).getByText('A-1077')).toBeInTheDocument()
    expect(within(nuevo).getByText('Teléfono')).toBeInTheDocument()
    expect(within(nuevo).getByText('Urgente')).toBeInTheDocument()
    expect(within(nuevo).getByText('Evidencia adjunta')).toBeInTheDocument()
    expect(within(metric('Tickets abiertos')).getByText('5')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nuevo ticket' })).toHaveFocus()
  })

  it('rechaza evidencia de más de 10 MB', async () => {
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
    const { user } = await openModal()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nuevo ticket' })).toHaveFocus()
  })
})
