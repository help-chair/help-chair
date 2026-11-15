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
