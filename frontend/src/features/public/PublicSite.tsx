import { Link } from '@/components/Link'
import { matchPath } from '@/lib/routing'
import EnterPage from './EnterPage'
import LandingPage from './LandingPage'
import { PublicLayout } from './PublicLayout'
import RegisterPage from './RegisterPage'
import StatusPage from './StatusPage'
import VerifyPage from './VerifyPage'

/** Sitio público (help-chair.com): landing, registro, verificación, progreso y entrada. */
export default function PublicSite({ path }: { path: string }) {
  const status = matchPath('/estado/:id', path)

  let page
  if (path === '/') page = <LandingPage />
  else if (path === '/registro') page = <RegisterPage />
  else if (path === '/verificar') page = <VerifyPage />
  else if (status) page = <StatusPage id={status.id} />
  else if (path === '/entrar') page = <EnterPage />
  else
    page = (
      <div className="space-y-3 text-center">
        <h1 className="text-xl font-bold">Página no encontrada</h1>
        <Link to="/" className="text-sm underline">
          Volver al inicio
        </Link>
      </div>
    )

  return <PublicLayout landing={path === '/'}>{page}</PublicLayout>
}
