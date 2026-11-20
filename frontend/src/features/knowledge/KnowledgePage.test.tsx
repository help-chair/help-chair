import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { crearArticulosDeEjemplo } from './data'
import { KnowledgePage } from './KnowledgePage'

// Carga inmediata con los artículos de ejemplo (sin la espera simulada de la red).
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
