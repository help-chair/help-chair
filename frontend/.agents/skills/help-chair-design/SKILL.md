---
name: help-chair-design
description: >-
  Sistema de diseño oficial de Help Chair (Service Desk). Define la paleta de colores ITIL v4,
  tipografías, escalas de espaciado, componentes UI (@/components/ui) y patrones visuales
  para garantizar consistencia en la interfaz del dashboard y microservicios.
---

# Help Chair Design System Skill

Esta skill guía a los agentes de IA y desarrolladores en la creación de vistas y componentes consistentes con la identidad de Help Chair y el estándar ITIL v4.

---

## 🎨 Paleta de Colores y Semántica ITIL

Todo elemento visual en el frontend debe ceñirse a estos roles semánticos:

### 1. Colores de Estado ITIL v4
- **Informativo (Informational):** Eventos de rutina, tareas programadas, logs de auditoría.
  - Clases: `bg-itil-info/10 text-itil-info border-itil-info/20` o variante `<Badge variant="info">`
- **Advertencia (Warning):** Umbrales alcanzados (disco > 80%, memoria alta), retrasos potenciales en SLA.
  - Clases: `bg-itil-warning/10 text-itil-warning border-itil-warning/20` o `<Badge variant="warning">`
- **Excepción / Incidencia (Exception):** Caída total o parcial de servicio, fallos de API, ataques o errores críticos.
  - Clases: `bg-itil-exception/10 text-itil-exception border-itil-exception/20` o `<Badge variant="exception">`
- **Resuelto / SLA en Verde (Success):** Tickets resueltos, metas cumplidas, servicios operativos.
  - Clases: `bg-itil-success/10 text-itil-success border-itil-success/20` o `<Badge variant="success">`
- **Peticiones de Servicio (Requests):** Accesos, hardware nuevo, licencias, solicitudes estándar.
  - Clases: `bg-itil-request/10 text-itil-request border-itil-request/20` o `<Badge variant="request">`

### 2. Estructura y Superficies
- **Fondo de la aplicación:** `bg-slate-100` o `bg-background`
- **Tarjetas y paneles:** `bg-white border border-slate-200 shadow-sm rounded-xl`
- **Sidebar de navegación:** `bg-slate-900 text-slate-200 border-r border-slate-800`
- **Header:** `bg-white border-b border-slate-200 h-16`

---

## 🧩 Catálogo de Componentes Base (`src/components/ui/`)

Siempre reutiliza los componentes existentes en lugar de escribir etiquetas HTML genéricas con clases duplicadas:

### Botón (`Button`)
```tsx
import { Button } from '@/components/ui/button';

<Button variant="primary">Guardar Cambios</Button>
<Button variant="outline" size="sm">Cancelar</Button>
<Button variant="danger">Escalar a Incidente</Button>
```

### Etiquetas de Estado (`Badge`)
```tsx
import { Badge } from '@/components/ui/badge';

<Badge variant="exception">Excepción Crítica</Badge>
<Badge variant="warning">En Advertencia</Badge>
<Badge variant="info">Informativo</Badge>
<Badge variant="success">SLA Cumplido</Badge>
```

### Contenedores de Información (`Card`)
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Métricas de Gestión de Eventos</CardTitle>
    <CardDescription>Eventos recibidos en las últimas 24 horas</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Contenido del widget */}
  </CardContent>
</Card>
```

---

## 📋 Reglas de Implementación para el Agente
1. **No inventar estilos aislados:** Si necesitas un componente nuevo (ej. un `Modal` o un `Select`), créalo primero dentro de `src/components/ui/` con Tailwind y expórtalo.
2. **Iconografía:** Usa exclusivamente `lucide-react` con tamaño `size={16}` para botones/badges y `size={20}` a `size={24}` para tarjetas de métricas.
3. **Responsive & Mobile-ready:** Diseña con `grid grid-cols-1 md:grid-cols-4` para paneles de métricas y scroll horizontal `overflow-x-auto` para tablas de datos.
