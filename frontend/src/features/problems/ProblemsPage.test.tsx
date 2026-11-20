import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { crearDatosDeEjemplo } from './data'
import { ProblemsPage } from './ProblemsPage'

// Carga inmediata con los datos de ejemplo (sin la espera simulada de la red).
const cargarAlInstante = () => Promise.resolve(crearDatosDeEjemplo())

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

  it('registra un problema nuevo y valida los campos obligatorios', async () => {
    const user = await renderPage()

    await user.click(screen.getByRole('button', { name: 'Registrar problema' }))
    const dialogo = screen.getByRole('dialog', { name: 'Registrar problema' })
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar problema' }))
    expect(within(dialogo).getByText('Escribe un título para el problema.')).toBeInTheDocument()
    expect(within(dialogo).getByLabelText(/Título/)).toHaveFocus()

    await user.type(
      within(dialogo).getByLabelText(/Título/),
      'Proyectores del edificio C sin señal',
    )
    await user.type(
      within(dialogo).getByLabelText(/Descripción/),
      'Fallan cada lunes por la mañana.',
    )
    await user.click(within(dialogo).getByRole('button', { name: 'Registrar problema' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Problema PRB-017 registrado')
    expect(within(fila('PRB-017')).getByText('Registrado')).toBeInTheDocument()
    expect(within(indicador('Problemas abiertos')).getByText('6')).toBeInTheDocument()
  })

  it('pide la causa raíz antes de pasar a «Causa identificada»', async () => {
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

    expect(screen.getByRole('status')).toHaveTextContent('Causa raíz registrada en PRB-016.')
    expect(
      screen.getByText('El servidor de correo limita los adjuntos a 10 MB.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Publicar error conocido' })).toBeInTheDocument()
  })

  it('publica un error conocido con su solución temporal', async () => {
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-012')

    await user.click(screen.getByRole('button', { name: 'Publicar error conocido' }))
    const dialogo = screen.getByRole('dialog', { name: 'Publicar error conocido' })
    await user.type(
      within(dialogo).getByLabelText(/Solución temporal/),
      'Reintentar el cobro después de 30 segundos.',
    )
    await user.click(within(dialogo).getByRole('button', { name: 'Publicar error conocido' }))

    expect(screen.getByRole('status')).toHaveTextContent(
      'Error conocido KE-008 publicado para PRB-012.',
    )
    expect(screen.getByText('Reintentar el cobro después de 30 segundos.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Marcar como resuelto' })).toBeInTheDocument()
  })

  it('no deja vincular dos veces la misma incidencia', async () => {
    const user = await renderPage()
    await abrirDetalle(user, 'PRB-015')

    await user.click(screen.getByRole('button', { name: 'Vincular incidencia' }))
    const dialogo = screen.getByRole('dialog', { name: 'Vincular incidencia' })
    const campo = within(dialogo).getByLabelText(/ID de la incidencia/)
    await user.type(campo, 'tck-1045')
    await user.click(within(dialogo).getByRole('button', { name: 'Vincular incidencia' }))
    expect(within(dialogo).getByText('TCK-1045 ya está vinculada a PRB-015.')).toBeInTheDocument()

    await user.clear(campo)
    await user.type(campo, 'TCK-1050')
    await user.click(within(dialogo).getByRole('button', { name: 'Vincular incidencia' }))
    expect(screen.getByRole('status')).toHaveTextContent('Incidencia TCK-1050 vinculada a PRB-015.')
    expect(screen.getByText('TCK-1050')).toBeInTheDocument()
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
