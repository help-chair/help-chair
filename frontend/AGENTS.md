# Reglas de Diseño y Desarrollo para Agentes de IA · Help Chair Frontend

Cualquier agente de IA (Antigravity, OpenCode, Claude Code, Cursor) que genere, edite o refactorice código en `frontend/` DEBE cumplir estrictamente estas directrices.

---

## 🎨 1. Tokens de Diseño y Colores Semánticos

NO inventes clases de colores arbitrarias (evita `bg-purple-900`, `text-[#ff2200]`, etc.).
Usa exclusivamente las clases semánticas mapeadas en `tailwind.config.js`:

| Semántica       | Clase de Fondo                      | Clase de Texto            | Borde / Badge        | Uso ITIL v4                                  |
| --------------- | ----------------------------------- | ------------------------- | -------------------- | -------------------------------------------- |
| **Informativo** | `bg-itil-info` o `bg-blue-50`       | `text-blue-700`           | `border-blue-200`    | Eventos de sistema, backups, logins          |
| **Advertencia** | `bg-itil-warning` o `bg-amber-50`   | `text-amber-800`          | `border-amber-200`   | Umbrales de disco/CPU, pre-alertas           |
| **Excepción**   | `bg-itil-exception` o `bg-red-50`   | `text-red-700`            | `border-red-200`     | Caídas de servicio, fallos, incidentes P1/P2 |
| **Éxito / SLA** | `bg-itil-success` o `bg-emerald-50` | `text-emerald-700`        | `border-emerald-200` | Tickets resueltos, SLAs cumplidos            |
| **Petición**    | `bg-itil-request` o `bg-purple-50`  | `text-purple-700`         | `border-purple-200`  | Solicitudes estándar de catálogo             |
| **Primario**    | `bg-primary` (Indigo)               | `text-primary-foreground` | `border-border`      | Acciones principales, botones CTA            |

---

## 🧩 2. Uso Obligatorio de Componentes Base

Antes de crear elementos HTML crudos o estilos repetitivos, utiliza los componentes de `@/components/ui/`:

- **Botones:** `import { Button } from '@/components/ui/button'`
  - Variantes: `primary`, `secondary`, `outline`, `ghost`, `danger`.
  - Tamaños: `sm`, `md`, `lg`.
- **Badges / Etiquetas:** `import { Badge } from '@/components/ui/badge'`
  - Variantes ITIL: `info`, `warning`, `exception`, `success`, `request`, `default`.
- **Tarjetas:** `import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'`

---

## 🔤 3. Tipografía y Jerarquía

- **Fuente base:** Sistema sans-serif nativo definido en `index.css`.
- **Títulos de página/dashboard:** `text-xl font-bold text-slate-900`
- **Títulos de sección/tarjeta:** `text-base font-semibold text-slate-800`
- **Cuerpo de texto / descripciones:** `text-sm text-slate-600`
- **Metadatos, timestamps y badges:** `text-xs text-slate-400 font-medium`

---

## 📐 4. Espaciado y Radios de Borde

- **Radio estándar:** `rounded-xl` para contenedores y tarjetas (`Card`), `rounded-lg` para botones y controles, `rounded-full` para badges.
- **Separación de secciones:** `space-y-6` o `gap-6`.
- **Padding interno de tarjetas:** `p-5` o `p-6`.

---

## 📚 5. Vocabulario y Convenciones ITIL v4

- **Nunca uses "tickets" de forma genérica** si puedes ser específico:
  - Si es una falla de servicio -> **Incidencia** (`Incident`).
  - Si es un pedido de catálogo/usuario -> **Petición de Servicio** (`Service Request`).
  - Si es un error recurrente o causa raíz desconocida -> **Problema** (`Problem`).
- Los eventos del monitor son **Informativo**, **Advertencia** o **Excepción**.

---

## 🌐 6. Sitio público, dominios y API

El frontend es **una sola SPA y una sola imagen** para `help-chair.com` (sitio público) y `empresaN.help-chair.com` (Service Desk). Diseño: `docs/REGISTRO-EMPRESA.md`.

- **Nunca escribas un dominio ni una URL de API en el código.** El dominio base viene de `getRuntimeConfig().baseDomain` (`src/config/runtime.ts`); la URL de una empresa se arma con `tenantUrl(subdominio)`.
- **La API se llama con rutas relativas** (`/api/public/v1/...`, `/api/<servicio>/...`) desde `src/api/`. Prohibido `fetch` con URL absoluta y prohibido leer `VITE_API_*` en el código de la app (solo las usa el proxy de `vite.config.ts`).
- **Rutas:** usa `src/lib/routing.ts` y `<Link>` de `@/components/Link`. No agregues `react-router` ni otra librería de enrutado sin acordarlo con el equipo.
  - Sitio público: se registran en `features/public/PublicSite.tsx`.
  - Service Desk: se montan desde `Root.tsx`.
- **Secretos y contraseñas:** nunca se guardan en `localStorage`/`sessionStorage`. Solo el token de seguimiento del alta vive en `sessionStorage` (`features/public/tracking.ts`).
- **Tokens de la URL** (`/verificar`, `/activar`) son de un solo uso: no los repitas en logs ni los reenvíes en una segunda llamada (cuidado con la doble ejecución de `StrictMode`, ver `VerifyPage.tsx`).
- **Estados del Alta de Empresa (`docs/REGISTRO-EMPRESA.md`):** La pantalla de progreso (`/estado/:id`) debe manejar el ciclo oficial: `pendiente_verificacion` → `aprovisionando` → `activa` (o `error` con reintento).
- **Subdominios Reservados:** El registro debe validar contra la lista negra del gateway (`www`, `api`, `admin`, `app`, `mail`, `status`, `help`, `support`).
- **Autenticación en Memoria (D-24):** El JWT vive únicamente en el estado en memoria de React (`api/access.ts`); nunca se persiste en `localStorage`.
- **Accesibilidad:** las páginas públicas también deben cumplir WCAG 2.1 AA (etiquetas, `role="alert"`/`aria-live` para mensajes, foco visible).

---

## 🏛️ 7. Arquitectura Modular del Service Desk (`src/features/`)

El Service Desk sigue una **Feature-Driven Architecture** organizada estrictamente por prácticas ITIL v4:

```text
src/features/
├── public/     # 🌐 Portal público: Landing, Registro de empresa y Status
├── dashboard/  # 📊 Dashboard Central: Gateway del Service Desk y KPIs globales
├── events/     # ⚡ Equipo 1: Gestión de Eventos y Monitoreo en tiempo real
├── access/     # 🔐 Equipo 2: Gestión de Accesos, login de stack y usuarios/roles
├── requests/   # 📥 Equipo 3: Gestión de Peticiones, catálogo y solicitudes
├── incidents/  # 🚨 Equipo 4: Gestión de Incidencias, Kanban y matriz de prioridad
├── problems/   # 🛡️ Equipo 5: Gestión de Problemas, causa raíz y KEDB
└── knowledge/  # 📚 Equipo 5: Base de Conocimiento y autoservicio
```

### Reglas de Desarrollo de Módulos para Agentes:
1. **Cascarón Común Inmutable (`src/components/layout/ServiceDeskLayout.tsx`):**
   - El Sidebar, Header superior, badges del tenant y notificaciones viven en `ServiceDeskLayout`.
   - **PROHIBIDO** reescribir o duplicar el Sidebar o Header dentro de las páginas de cada módulo.
   - Tu módulo debe exportar un componente principal autónomo (ej. `export function IncidentsPage()`).
2. **Conexión en `src/App.tsx`:**
   - Para registrar o activar un módulo, se añade su clave al tipo `TabKey` en `ServiceDeskLayout.tsx` y se monta condicionalmente en `src/App.tsx`.
3. **Formularios e Inputs:**
   - Todo formulario debe usar los componentes estandarizados de `@/components/ui/form` (`Field`, `Input`, `Select`, `Textarea`), que ya cuentan con los estados visuales *Default*, *Focus*, *Error*, y accesibilidad WCAG (`aria-invalid`, `aria-describedby`).
4. **Mocks y Contratos:**
   - Mientras el microservicio backend publica su API oficial en `contracts/<servicio>/openapi.yaml`, define los datos simulados en un archivo local `data.ts` dentro de tu carpeta `features/<servicio>/`. Cuando el contrato exista, genera los tipos en `types.ts` a partir del OpenAPI.

---

## 📸 8. Evidencias de Diseño y Capturas de Figma (`frontend/docs/`)

Para mantener el orden del monorepo y evitar conflictos entre sistemas operativos (Linux y Windows):

- **Ubicación obligatoria:** Las capturas de pantalla, flujos exportados y evidencias de diseño en Figma deben guardarse exclusivamente dentro de `frontend/docs/<practica>/`:
  ```text
  frontend/docs/
  ├── access/       # Capturas del módulo de Accesos (Equipo 2)
  ├── dashboard/    # Capturas del Dashboard central / Home
  ├── events/       # Capturas del Monitor de Gestión de Eventos (Equipo 1)
  ├── incidents/    # Capturas de la Gestión de Incidencias (Equipo 4)
  ├── knowledge/    # Capturas de la Base de Conocimiento (Equipo 5)
  ├── problems/     # Capturas de la Gestión de Problemas (Equipo 5)
  ├── public/       # Capturas del Portal Público / Landing / Registro
  └── requests/     # Capturas de la Gestión de Peticiones (Equipo 3)
  ```
- **Convención de nombres de archivo:**
  - Nombres estrictamente en **minúsculas** en formato kebab-case (ejemplo: `dashboard-incidentes.png`, `modal-nuevo-ticket.png`).
  - **PROHIBIDO** usar espacios, mayúsculas, tildes o caracteres especiales (evita rutas como `Diseño/`, `Captura 1.png` o caracteres ilegales en Windows/Git como `<` o `>`).
  - Esta carpeta es **únicamente para evidencias gráficas y documentación complementaria**. Queda terminantemente **PROHIBIDO** colocar proyectos de Vite, archivos `package.json` o código ejecutable dentro de `frontend/docs/`.

---

## ♿ 9. Calidad, Accesibilidad y Microcopy

Todo desarrollo en el frontend debe apegarse a los estándares de experiencia y accesibilidad detallados en la skill `help-chair-design` (`frontend/.agents/skills/help-chair-design/SKILL.md`):

1. **Microcopy Orientado a la Acción:**
   - Botones con verbos explícitos y en voz activa (`Guardar Cambios`, `Crear Petición`, `Escalar a Nivel 2`), nunca textos genéricos como `Enviar` o `Aceptar`.
   - Coherencia total entre la acción y el mensaje de confirmación/toast.
2. **Tratamiento Obligatorio de Estados:**
   - Todo componente o tabla con datos asíncronos debe manejar sus 3 estados: **Carga** (`Skeleton`/spinner), **Vacío** (`Empty State` con llamada a la acción) y **Error** (explicativo y con botón de reintento).
3. **Estándares de Accesibilidad (WCAG 2.1 AA):**
   - Identificadores accesibles en formularios con `useId()` de React.
   - Navegación 100% operable por teclado con foco visible.
   - Modales con `role="dialog"`, `aria-modal="true"` y cierre con tecla `Escape`.
   - Tablas con scroll horizontal responsivo (`overflow-x-auto` y `min-w-[640px]`) para no romper pantallas móviles o tablets.


