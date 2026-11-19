// @vitest-environment jsdom
import { render, screen, cleanup } from '@testing-library/react'
import { withRole, useHasRole } from '@/auth/roleGuard'
import type { RolId } from '@/features/access/types'

afterEach(() => {
  cleanup()
})

function DummyComponent() {
  return <div data-testid="allowed">Allowed</div>
}

describe('withRole HOC', () => {
  const Allowed = withRole(DummyComponent, ['administrador'])

  test('renders wrapped component when role is allowed', () => {
    render(<Allowed currentRole="administrador" />)
    expect(screen.getByTestId('allowed')).toBeInTheDocument()
  })

  test('renders "no permission" when role is disallowed', () => {
    const { container } = render(<Allowed currentRole="usuario_final" />)
    expect(container.querySelector('[data-testid="allowed"]')).toBeNull()
    expect(container.textContent).toContain('No tienes permiso')
  })

  test('renders "no permission" when role is undefined', () => {
    const { container } = render(<Allowed currentRole={undefined} />)
    expect(container.querySelector('[data-testid="allowed"]')).toBeNull()
  })
})

describe('useHasRole hook', () => {
  function TestHook({ roles, userRole }: { roles: RolId[]; userRole: RolId | undefined }) {
    const has = useHasRole(roles, userRole)
    return <div data-testid="hook-result">{has ? 'true' : 'false'}</div>
  }

  test('returns true for a matching role', () => {
    render(<TestHook roles={['agente_n2', 'usuario_final']} userRole="agente_n2" />)
    expect(screen.getByTestId('hook-result')).toHaveTextContent('true')
  })

  test('returns false for a non-matching role', () => {
    render(<TestHook roles={['administrador']} userRole="usuario_final" />)
    expect(screen.getByTestId('hook-result')).toHaveTextContent('false')
  })

  test('returns false when userRole is undefined', () => {
    render(<TestHook roles={['administrador']} userRole={undefined} />)
    expect(screen.getByTestId('hook-result')).toHaveTextContent('false')
  })
})
