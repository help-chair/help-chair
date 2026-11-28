import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CancelReasonDialog } from './CancelReasonDialog'
import { buildCancelReason } from './options'
import { SatisfactionSurvey } from './SatisfactionSurvey'
import { SurveySummary } from './SurveySummary'

describe('SatisfactionSurvey', () => {
  it('pide una calificación antes de guardar', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <SatisfactionSurvey
        subject="REQ-0012"
        submitLabel="Guardar calificación"
        onSubmit={onSubmit}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Guardar calificación' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Elige una calificación del 1 al 5.')
    expect(screen.getByRole('radio', { name: 'Muy mala' })).toHaveFocus()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('envía la calificación con el comentario sin espacios sobrantes', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(
      <SatisfactionSurvey
        subject="REQ-0012"
        submitLabel="Guardar calificación"
        onSubmit={onSubmit}
      />,
    )

    await user.click(screen.getByRole('radio', { name: 'Buena' }))
    await user.type(screen.getByLabelText(/quieres contarnos algo más/i), '  Muy rápido  ')
    await user.click(screen.getByRole('button', { name: 'Guardar calificación' }))

    expect(onSubmit).toHaveBeenCalledWith({ rating: 4, comment: 'Muy rápido' })
  })

  it('muestra el error y permite reintentar si no se pudo guardar', async () => {
    const user = userEvent.setup()
    const onSubmit = vi
      .fn()
      .mockRejectedValueOnce(new Error('red'))
      .mockResolvedValueOnce(undefined)
    render(
      <SatisfactionSurvey
        subject="REQ-0012"
        submitLabel="Guardar calificación"
        onSubmit={onSubmit}
      />,
    )

    await user.click(screen.getByRole('radio', { name: 'Excelente' }))
    await user.click(screen.getByRole('button', { name: 'Guardar calificación' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/no pudimos guardar/i)
    await user.click(screen.getByRole('button', { name: 'Intentar de nuevo' }))
    expect(onSubmit).toHaveBeenCalledTimes(2)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('ofrece la acción secundaria', async () => {
    const user = userEvent.setup()
    const onReopen = vi.fn()
    render(
      <SatisfactionSurvey
        subject="REQ-0012"
        submitLabel="Calificar y cerrar petición"
        onSubmit={vi.fn()}
        secondaryAction={{ label: 'No quedó resuelta: reabrir', onClick: onReopen }}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'No quedó resuelta: reabrir' }))

    expect(onReopen).toHaveBeenCalled()
  })
})

describe('SurveySummary', () => {
  it('muestra la calificación y el comentario', () => {
    render(
      <SurveySummary
        answer={{ rating: 2, comment: 'Tardó mucho.', answeredAt: '2026-11-20T10:00:00Z' }}
      />,
    )

    expect(screen.getByText('Mala')).toBeInTheDocument()
    expect(screen.getByText('(2 de 5)')).toBeInTheDocument()
    expect(screen.getByText('«Tardó mucho.»')).toBeInTheDocument()
  })
})

describe('CancelReasonDialog', () => {
  function renderDialog() {
    const onConfirm = vi.fn()
    render(
      <CancelReasonDialog
        open
        subject="REQ-0014 · Instalación de programa"
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />,
    )
    return onConfirm
  }

  it('pide elegir un motivo', async () => {
    const user = userEvent.setup()
    const onConfirm = renderDialog()

    await user.click(screen.getByRole('button', { name: 'Cancelar petición' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Elige un motivo.')
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('con «Otro motivo» exige escribirlo', async () => {
    const user = userEvent.setup()
    const onConfirm = renderDialog()

    await user.click(screen.getByRole('radio', { name: 'Otro motivo' }))
    await user.click(screen.getByRole('button', { name: 'Cancelar petición' }))

    expect(screen.getByText('Escribe el motivo de la cancelación.')).toBeInTheDocument()
    expect(screen.getByLabelText(/cuéntanos el motivo/i)).toHaveFocus()

    await user.type(screen.getByLabelText(/cuéntanos el motivo/i), 'Cambié de área')
    await user.click(screen.getByRole('button', { name: 'Cancelar petición' }))

    expect(onConfirm).toHaveBeenCalledWith('Cambié de área')
  })

  it('une el motivo y el detalle', async () => {
    const user = userEvent.setup()
    const onConfirm = renderDialog()

    await user.click(screen.getByRole('radio', { name: 'La resolví por mi cuenta' }))
    await user.type(screen.getByLabelText(/detalles/i), 'Reinicié el equipo')
    await user.click(screen.getByRole('button', { name: 'Cancelar petición' }))

    expect(onConfirm).toHaveBeenCalledWith('La resolví por mi cuenta: Reinicié el equipo')
  })
})

describe('buildCancelReason', () => {
  it('respeta el máximo de 255 caracteres del contrato', () => {
    expect(buildCancelReason('Otro motivo', 'x'.repeat(300))).toHaveLength(255)
    expect(buildCancelReason('Ya no la necesito', '   ')).toBe('Ya no la necesito')
  })
})
