import {
  Activity,
  ArrowRight,
  BookOpen,
  Boxes,
  CheckCircle2,
  Flame,
  Inbox,
  KeyRound,
  LayoutDashboard,
  LogIn,
  MailCheck,
  Rocket,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from 'lucide-react'
import { Link } from '@/components/Link'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { DashboardPreview } from './DashboardPreview'
import { SubdomainClaim } from './SubdomainClaim'

interface Practice {
  title: string
  text: string
  icon: LucideIcon
  tone: string
}

// Colores semánticos ITIL del sistema de diseño (frontend/DESIGN.md).
const PRACTICES: Practice[] = [
  {
    title: 'Gestión de Eventos',
    text: 'Monitorea tu infraestructura y clasifica cada evento como informativo, advertencia o excepción.',
    icon: Activity,
    tone: 'bg-blue-50 text-blue-700',
  },
  {
    title: 'Peticiones de servicio',
    text: 'Un catálogo de autoservicio para pedir equipo, software o accesos y seguir su avance.',
    icon: Inbox,
    tone: 'bg-purple-50 text-purple-700',
  },
  {
    title: 'Incidencias',
    text: 'Registra fallas, calcula su prioridad y restablece el servicio antes de que venza el SLA.',
    icon: Flame,
    tone: 'bg-red-50 text-red-700',
  },
  {
    title: 'Problemas',
    text: 'Encuentra la causa raíz de las fallas que se repiten y documenta soluciones temporales.',
    icon: ShieldAlert,
    tone: 'bg-amber-50 text-amber-800',
  },
  {
    title: 'Base de Conocimiento',
    text: 'Artículos y soluciones para que tus usuarios y agentes resuelvan más rápido.',
    icon: BookOpen,
    tone: 'bg-emerald-50 text-emerald-700',
  },
  {
    title: 'Accesos y roles',
    text: 'Usuarios, roles y permisos por empresa, con inicio de sesión seguro.',
    icon: KeyRound,
    tone: 'bg-slate-100 text-slate-700',
  },
]

const BENEFITS: { title: string; text: string; icon: LucideIcon }[] = [
  {
    title: 'Tu propio espacio',
    text: 'Cada empresa recibe su subdominio y un stack aislado, con sus propios contenedores y bases de datos.',
    icon: Boxes,
  },
  {
    title: 'Alineado a ITIL v4',
    text: 'Usa el vocabulario y las prácticas de ITIL v4: eventos, peticiones, incidencias y problemas.',
    icon: ShieldCheck,
  },
  {
    title: 'Listo en minutos',
    text: 'Te registras, verificas tu correo y un asistente te guía para configurar servicios, SLA y usuarios.',
    icon: Rocket,
  },
]

const STEPS: { title: string; text: string; icon: LucideIcon }[] = [
  {
    title: 'Registra tu empresa',
    text: 'Elige tu subdominio y captura los datos mínimos.',
    icon: Sparkles,
  },
  {
    title: 'Verifica tu correo',
    text: 'Al confirmarlo, creamos tu stack aislado.',
    icon: MailCheck,
  },
  {
    title: 'Activa tu cuenta',
    text: 'Define tu contraseña de administrador.',
    icon: KeyRound,
  },
  {
    title: 'Entra a tu dashboard',
    text: 'Empiezas viendo tus eventos en tiempo real.',
    icon: LayoutDashboard,
  },
]

const FACTS = [
  { value: '7', label: 'equipos de desarrollo' },
  { value: '6', label: 'módulos ITIL v4' },
  { value: '1', label: 'stack aislado por empresa' },
]

const container = 'mx-auto max-w-6xl px-4'

function SectionHeading({
  id,
  eyebrow,
  title,
  text,
}: {
  id: string
  eyebrow: string
  title: string
  text: string
}) {
  return (
    <div className="mx-auto max-w-2xl space-y-3 text-center">
      <p className="text-xs font-semibold uppercase tracking-wider text-primary">{eyebrow}</p>
      <h2 id={id} className="scroll-mt-24 text-2xl font-bold text-slate-900 sm:text-3xl">
        {title}
      </h2>
      <p className="text-base text-slate-600">{text}</p>
    </div>
  )
}

export default function LandingPage() {
  return (
    <>
      {/* Portada */}
      <section
        aria-labelledby="titulo-principal"
        className="border-b border-slate-200 bg-gradient-to-b from-indigo-50 via-white to-slate-50"
      >
        <div className={`${container} grid items-center gap-12 py-14 lg:grid-cols-2 lg:py-20`}>
          <div className="space-y-6">
            <Badge variant="request" className="w-fit">
              Service Desk multiempresa · ITIL v4
            </Badge>
            <h1
              id="titulo-principal"
              className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl"
            >
              La mesa de ayuda de tu empresa, en tu propio subdominio
            </h1>
            <p className="max-w-xl text-lg text-slate-600">
              Help Chair reúne eventos, peticiones, incidencias y problemas en un solo Service Desk.
              Registra tu empresa y en minutos tendrás tu espacio listo para atender a tus usuarios.
            </p>
            <SubdomainClaim />
            <p className="text-sm text-slate-600">
              ¿Tu empresa ya usa Help Chair?{' '}
              <Link
                to="/entrar"
                className="inline-flex items-center gap-1 font-semibold text-primary hover:underline"
              >
                <LogIn size={14} aria-hidden="true" />
                Entrar a mi empresa
              </Link>
            </p>
          </div>
          <DashboardPreview />
        </div>
      </section>

      {/* Qué hacemos */}
      <section aria-labelledby="que-hacemos" className={`${container} py-16`}>
        <SectionHeading
          id="que-hacemos"
          eyebrow="Qué hacemos"
          title="Todo tu Service Desk en un solo lugar"
          text="Cada práctica de ITIL v4 es un módulo conectado con los demás: un evento puede convertirse en petición o incidencia, y una incidencia que se repite, en un problema."
        />
        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PRACTICES.map((practice) => (
            <li key={practice.title}>
              <Card className="flex h-full gap-4 p-5">
                <span className={`h-fit rounded-lg p-2.5 ${practice.tone}`}>
                  <practice.icon size={20} aria-hidden="true" />
                </span>
                <div className="space-y-1">
                  <h3 className="text-base font-semibold text-slate-800">{practice.title}</h3>
                  <p className="text-sm text-slate-600">{practice.text}</p>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      </section>

      {/* Por qué Help Chair */}
      <section aria-labelledby="por-que" className="border-y border-slate-200 bg-white">
        <div className={`${container} py-16`}>
          <h2 id="por-que" className="sr-only">
            Por qué Help Chair
          </h2>
          <ul className="grid gap-8 md:grid-cols-3">
            {BENEFITS.map((benefit) => (
              <li key={benefit.title} className="space-y-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
                  <benefit.icon size={20} aria-hidden="true" />
                </span>
                <h3 className="text-base font-semibold text-slate-800">{benefit.title}</h3>
                <p className="text-sm text-slate-600">{benefit.text}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Cómo funciona */}
      <section aria-labelledby="como-funciona" className={`${container} py-16`}>
        <SectionHeading
          id="como-funciona"
          eyebrow="Cómo funciona"
          title="De tu registro a tu dashboard en cuatro pasos"
          text="Solo pedimos lo mínimo para empezar. Los servicios, prioridades, SLA y usuarios los configuras después, dentro de tu help desk."
        />
        <ol className="mt-10 grid gap-4 md:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title}>
              <Card className="relative h-full space-y-3 p-5">
                <div className="flex items-center justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-primary">
                    <step.icon size={18} aria-hidden="true" />
                  </span>
                  <span className="text-xs font-semibold text-slate-400">Paso {index + 1}</span>
                </div>
                <h3 className="text-base font-semibold text-slate-800">{step.title}</h3>
                <p className="text-sm text-slate-600">{step.text}</p>
              </Card>
            </li>
          ))}
        </ol>
      </section>

      {/* Quiénes somos */}
      <section aria-labelledby="quienes-somos" className="border-t border-slate-200 bg-white">
        <div className={`${container} grid gap-10 py-16 lg:grid-cols-2 lg:items-center`}>
          <div className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Quiénes somos
            </p>
            <h2
              id="quienes-somos"
              className="scroll-mt-24 text-2xl font-bold text-slate-900 sm:text-3xl"
            >
              Un proyecto hecho por estudiantes del CETI
            </h2>
            <p className="text-base text-slate-600">
              Help Chair es un proyecto académico-profesional del Centro de Enseñanza Técnica
              Industrial. Siete equipos construyen cada práctica como un microservicio
              independiente, con su propia base de datos, y las conectan mediante contratos de API.
            </p>
            <ul className="space-y-2 text-sm text-slate-700">
              {[
                'Microservicios en contenedores, orquestados con Kubernetes.',
                'Con la accesibilidad WCAG 2.1 AA como meta de diseño.',
                'Un solo repositorio con revisiones de código entre equipos.',
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <CheckCircle2
                    size={16}
                    aria-hidden="true"
                    className="mt-0.5 shrink-0 text-emerald-600"
                  />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <dl className="grid grid-cols-3 gap-4">
            {FACTS.map((fact) => (
              <Card key={fact.label} className="flex flex-col-reverse p-5 text-center">
                <dt className="mt-1 text-xs font-medium text-slate-500">{fact.label}</dt>
                <dd className="text-3xl font-bold text-primary">{fact.value}</dd>
              </Card>
            ))}
          </dl>
        </div>
      </section>

      {/* Llamado final */}
      <section aria-labelledby="empieza" className={`${container} py-16`}>
        <div className="flex flex-col items-start gap-6 rounded-2xl bg-gradient-to-r from-indigo-700 via-indigo-800 to-slate-900 p-8 text-white shadow-sm md:flex-row md:items-center md:justify-between md:p-10">
          <div className="space-y-2">
            <h2 id="empieza" className="text-2xl font-bold">
              ¿Listo para ordenar el soporte de tu empresa?
            </h2>
            <p className="max-w-xl text-sm text-indigo-100">
              Registra tu empresa hoy. Si ya tienes cuenta, entra con tu correo o con el subdominio
              de tu empresa.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/registro"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm transition-colors hover:bg-indigo-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Registrar mi empresa
              <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <Link
              to="/entrar"
              className="inline-flex items-center gap-2 rounded-lg border border-white/30 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <LogIn size={16} aria-hidden="true" />
              Entrar a mi empresa
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
