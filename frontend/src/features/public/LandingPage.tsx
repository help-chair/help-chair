import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Link } from '@/components/Link'
import { ctaClass } from './PublicLayout'

const features = [
  {
    title: 'Alineado a ITIL v4',
    text: 'Eventos, peticiones, incidencias y problemas con el vocabulario y las prácticas de ITIL v4.',
  },
  {
    title: 'Tu propio stack',
    text: 'Cada empresa recibe un entorno aislado, con sus propios contenedores y bases de datos.',
  },
  {
    title: 'Listo en minutos',
    text: 'Regístrate, verifica tu correo y configura tu help desk con un asistente guiado.',
  },
]

const steps = [
  'Registra tu empresa con los datos mínimos.',
  'Verifica tu correo y espera a que se cree tu stack.',
  'Activa tu cuenta de administrador y configura servicios, SLA y usuarios.',
]

export default function LandingPage() {
  return (
    <div className="space-y-14">
      <section className="space-y-5 text-center">
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
          El help desk que se adapta a tu empresa
        </h1>
        <p className="mx-auto max-w-2xl text-base text-slate-600">
          Help Chair es un Service Desk multiempresa: cada organización obtiene su propio espacio,
          configurado con sus servicios, prioridades y SLA.
        </p>
        <Link to="/registro" className={ctaClass}>
          Registrar mi empresa
        </Link>
      </section>

      <section aria-labelledby="que-es" className="grid gap-4 sm:grid-cols-3">
        <h2 id="que-es" className="sr-only">
          Qué ofrece Help Chair
        </h2>
        {features.map((f) => (
          <Card key={f.title}>
            <CardHeader>
              <CardTitle>{f.title}</CardTitle>
              <CardDescription>{f.text}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </section>

      <section aria-labelledby="como-funciona" className="space-y-4">
        <h2 id="como-funciona" className="text-xl font-bold text-slate-900">
          Cómo funciona
        </h2>
        <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-700">
          {steps.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="quienes-somos">
        <Card>
          <CardHeader>
            <CardTitle>
              <span id="quienes-somos">Quiénes somos</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">
              Help Chair es un proyecto académico-profesional desarrollado por equipos del Centro de
              Enseñanza Técnica Industrial (CETI).
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
