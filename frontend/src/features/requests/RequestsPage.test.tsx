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

  it('registra la petición y la muestra en «Mis peticiones» con aprobación pendiente', async () => {
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
    expect(within(card).getAllByText(/aprobación pendiente/i)[0]).toBeInTheDocument()
    expect(within(card).getByRole('listitem', { current: 'step' })).toHaveTextContent(
      /aprobación pendiente/i,
    )
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

    await user.click(screen.getByRole('button', { name: /aprobación pendiente/i }))

    expect(screen.getByText('REQ-0015')).toBeInTheDocument()
    expect(screen.queryByText('REQ-0014')).not.toBeInTheDocument()
  })
})
