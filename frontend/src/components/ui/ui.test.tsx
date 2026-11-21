import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Badge } from './badge'
import { Button } from './button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card'
import { Field, Input, Select, Textarea } from './form'
import { Modal } from './modal'

describe('Button', () => {
  it('renderiza el texto y ejecuta el clic', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(<Button onClick={onClick}>Guardar</Button>)

    await user.click(screen.getByRole('button', { name: 'Guardar' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('aplica la variante danger y respeta disabled', () => {
    render(
      <Button variant="danger" disabled>
        Eliminar
      </Button>,
    )

    const button = screen.getByRole('button', { name: 'Eliminar' })
    expect(button).toBeDisabled()
    expect(button.className).toContain('bg-itil-exception')
  })
})

describe('Badge', () => {
  it('renderiza el contenido y aplica la variante semántica', () => {
    render(<Badge variant="exception">Excepción</Badge>)

    const badge = screen.getByText('Excepción')
    expect(badge.className).toContain('bg-red-50')
    expect(badge.className).toContain('text-red-700')
  })
})

describe('Card', () => {
  it('compone header, título, descripción, contenido y footer', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Título</CardTitle>
          <CardDescription>Descripción</CardDescription>
        </CardHeader>
        <CardContent>Contenido</CardContent>
        <CardFooter>Pie</CardFooter>
      </Card>,
    )

    expect(screen.getByRole('heading', { name: 'Título' })).toBeInTheDocument()
    expect(screen.getByText('Descripción')).toBeInTheDocument()
    expect(screen.getByText('Contenido')).toBeInTheDocument()
    expect(screen.getByText('Pie')).toBeInTheDocument()
  })
})

describe('Field y controles', () => {
  it('asocia la etiqueta al control y muestra el mensaje de error', () => {
    render(
      <Field label="Correo" htmlFor="correo" required error="Requerido.">
        <Input id="correo" invalid aria-describedby="correo-description" />
      </Field>,
    )

    const input = screen.getByLabelText(/correo/i)
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAttribute('aria-describedby', 'correo-description')
    expect(screen.getByText('Requerido.')).toBeInTheDocument()
    expect(screen.getByText('Requerido.').id).toBe('correo-description')
  })

  it('renderiza Textarea y Select', () => {
    render(
      <Field label="Nota" htmlFor="nota">
        <Textarea id="nota" />
      </Field>,
    )
    expect(screen.getByLabelText('Nota')).toBeInTheDocument()

    render(
      <Select aria-label="Departamento">
        <option value="sistemas">Sistemas</option>
      </Select>,
    )
    expect(screen.getByRole('combobox', { name: 'Departamento' })).toBeInTheDocument()
  })
})

describe('Modal', () => {
  it('renderiza el diálogo con aria-modal y título', () => {
    render(
      <Modal open title="Nuevo ticket" description="Rellena los campos." onClose={vi.fn()}>
        <p>Formulario</p>
      </Modal>,
    )

    expect(screen.getByRole('dialog', { name: 'Nuevo ticket' })).toHaveAttribute(
      'aria-modal',
      'true',
    )
    expect(screen.getByText('Rellena los campos.')).toBeInTheDocument()
  })

  it('no renderiza nada cuando está cerrado', () => {
    render(
      <Modal open={false} title="Oculto" onClose={vi.fn()}>
        <p>Contenido</p>
      </Modal>,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cierra con Escape y con el botón de cerrar', () => {
    const onClose = vi.fn()
    render(
      <Modal open title="Modal" onClose={onClose}>
        <p>Contenido</p>
      </Modal>,
    )

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
    expect(onClose).toHaveBeenCalledTimes(2)
  })
})
