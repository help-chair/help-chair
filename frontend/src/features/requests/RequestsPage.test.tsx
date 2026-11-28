import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RequestsPage } from './RequestsPage'

describe('RequestsPage', () => {
  it('muestra el catálogo con el tiempo de entrega y si requiere aprobación', () => {
    render(<RequestsPage />)

    const card = screen.getByRole('heading', { name: 'Acceso a servidor' }).closest('li')!
    expect(within(card).getByText(/entrega: 1 día hábil/i)).toBeInTheDocument()
    expect(within(card).getByText(/requiere aprobación/i)).toBeInTheDocument()
  })

  it('filtra el catálogo por categoría', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: 'Telefonía' }))

    expect(
      screen.getByRole('heading', { name: 'Línea o extensión telefónica' }),
    ).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Acceso a servidor' })).not.toBeInTheDocument()
  })

  it('no envía el formulario si faltan campos obligatorios', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: 'Solicitar Acceso a servidor' }))
    await user.click(screen.getByRole('button', { name: /enviar petición/i }))

    expect(screen.getByText('Escribe tu nombre completo.')).toBeInTheDocument()
    expect(screen.getByText('Completa el campo «Servidor».')).toBeInTheDocument()
    expect(screen.getByLabelText(/nombre completo/i)).toHaveFocus()
  })

  it('registra la petición como nueva y en espera de aprobación', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: 'Solicitar Acceso a servidor' }))
    await user.type(screen.getByLabelText(/nombre completo/i), 'Daniela Ruiz')
    await user.selectOptions(screen.getByLabelText(/departamento/i), 'Sistemas')
    await user.type(screen.getByLabelText(/^servidor/i), 'srv-app-01')
    await user.selectOptions(screen.getByLabelText(/nivel de acceso/i), 'Solo lectura')
    await user.type(
      screen.getByLabelText(/descripción o justificación/i),
      'Necesito revisar los logs de la aplicación.',
    )
    await user.click(screen.getByRole('button', { name: /enviar petición/i }))

    expect(screen.getByRole('status')).toHaveTextContent('Tu petición REQ-0016 fue enviada')
    const card = screen.getByText('REQ-0016').closest('li')!
    expect(within(card).getByText('Daniela Ruiz')).toBeInTheDocument()
    expect(within(card).getByText('Por aprobar')).toBeInTheDocument()
    expect(within(card).getByRole('listitem', { current: 'step' })).toHaveTextContent(/aprobación/i)
  })

  it('califica una petición resuelta y la cierra', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: /mis peticiones/i }))
    const card = screen.getByText('REQ-0012').closest('li')!
    expect(within(card).getByRole('listitem', { current: 'step' })).toHaveTextContent(/resuelta/i)

    await user.click(within(card).getByRole('radio', { name: 'Excelente' }))
    await user.click(within(card).getByRole('button', { name: 'Calificar y cerrar petición' }))

    expect(within(card).queryByRole('listitem', { current: 'step' })).not.toBeInTheDocument()
    expect(within(card).getByRole('list', { name: /línea de vida/i })).toHaveTextContent(
      'Cerrada (completado)',
    )
    expect(within(card).getByRole('status')).toHaveTextContent(/gracias por tu calificación/i)
    expect(within(card).getByText(/calificaste la atención como/i)).toHaveTextContent('Excelente')
    expect(within(card).queryByRole('radio')).not.toBeInTheDocument()
  })

  it('reabre una petición que no quedó resuelta', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: /mis peticiones/i }))
    const card = screen.getByText('REQ-0012').closest('li')!
    await user.click(within(card).getByRole('button', { name: 'No quedó resuelta: reabrir' }))

    expect(within(card).getByText('Reabierta')).toBeInTheDocument()
    expect(within(card).queryByRole('radio')).not.toBeInTheDocument()
    expect(within(card).getByRole('button', { name: /cancelar petición/i })).toBeInTheDocument()
  })

  it('cancela una petición y guarda el motivo', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: /mis peticiones/i }))
    const card = screen.getByText('REQ-0014').closest('li')!
    await user.click(within(card).getByRole('button', { name: /cancelar petición/i }))

    const dialog = screen.getByRole('dialog', { name: 'Cancelar petición' })
    await user.click(within(dialog).getByRole('radio', { name: 'Ya no la necesito' }))
    await user.click(within(dialog).getByRole('button', { name: 'Cancelar petición' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(within(card).getByText('Cancelada')).toBeInTheDocument()
    expect(within(card).getByText('Motivo: Ya no la necesito')).toBeInTheDocument()
    expect(
      within(card).queryByRole('button', { name: /cancelar petición/i }),
    ).not.toBeInTheDocument()
  })

  it('no ofrece la encuesta en peticiones cerradas que ya se calificaron', async () => {
    const user = userEvent.setup()
    render(<RequestsPage />)

    await user.click(screen.getByRole('button', { name: /mis peticiones/i }))
    const card = screen.getByText('REQ-0011').closest('li')!

    expect(within(card).queryByRole('radio')).not.toBeInTheDocument()
    expect(within(card).getByText(/calificaste la atención como/i)).toHaveTextContent('Excelente')
  })

  it('no muestra la cola de atención para el usuario final', () => {
    render(<RequestsPage />)

    expect(screen.queryByRole('button', { name: /cola de atención/i })).not.toBeInTheDocument()
  })

  it('muestra la cola de atención para los agentes', () => {
    render(<RequestsPage puedeGestionar />)

    expect(screen.getByRole('button', { name: /cola de atención/i })).toBeInTheDocument()
  })

  it('filtra la cola por estado', async () => {
    const user = userEvent.setup()
    render(<RequestsPage puedeGestionar />)

    await user.click(screen.getByRole('button', { name: /cola de atención/i }))
    expect(screen.getByText('REQ-0015')).toBeInTheDocument()
    expect(screen.getByText('REQ-0014')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Nueva' }))

    const table = screen.getByRole('table')
    expect(within(table).getByText('REQ-0015')).toBeInTheDocument()
    expect(within(table).getByText('Por aprobar')).toBeInTheDocument()
    expect(within(table).queryByText('REQ-0014')).not.toBeInTheDocument()
  })
})
