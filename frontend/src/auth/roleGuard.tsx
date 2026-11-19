// Role-based guard utilities for the frontend.
// Provides a higher-order component (HOC) and a React hook to restrict
// rendering based on the logged-in user's role.
//
// NOTE: The current app does NOT use React Router or a global AuthContext.
// Session state lives as local state in App.tsx.  Therefore:
//   • `useHasRole` accepts an explicit `userRole` argument.
//   • `withRole` renders a "no permission" banner instead of a <Navigate>.

import React from 'react'
import type { RolId } from '@/features/access/types'

// ---------------------------------------------------------------------------
// Hook – returns true when `userRole` is included in `allowedRoles`.
// ---------------------------------------------------------------------------

/**
 * Checks whether the given user role is among the allowed roles.
 *
 * @param allowedRoles - List of roles that have access.
 * @param userRole     - The active user's role (may be undefined when logged out).
 * @returns `true` if the user holds one of the allowed roles.
 */
export function useHasRole(
  allowedRoles: RolId[],
  userRole: RolId | undefined,
): boolean {
  return !!userRole && allowedRoles.includes(userRole)
}

// ---------------------------------------------------------------------------
// HOC – wraps a component so it only renders for allowed roles.
// ---------------------------------------------------------------------------

/** Props injected by `withRole` to supply the current role. */
interface WithRoleInjectedProps {
  /** The current user's role. Must be passed by the parent. */
  currentRole?: RolId
}

/**
 * Higher-order component that renders `Component` only when the user holds
 * one of the `allowedRoles`.  When the role is missing or disallowed it
 * renders a "no permission" message instead.
 *
 * Usage:
 * ```tsx
 * const ProtectedPage = withRole(MyPage, ['administrador', 'agente_n2'])
 * <ProtectedPage currentRole={sesion.usuario.rol} />
 * ```
 */
export function withRole<P extends object>(
  Component: React.ComponentType<P>,
  allowedRoles: RolId[],
) {
  return function RoleProtected(props: P & WithRoleInjectedProps) {
    const { currentRole, ...rest } = props
    if (!currentRole || !allowedRoles.includes(currentRole)) {
      return (
        <div className="p-4 text-center text-red-600">
          No tienes permiso para ver esta sección.
        </div>
      )
    }
    return <Component {...(rest as P)} />
  }
}
