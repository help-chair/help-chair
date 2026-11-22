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
4. **Arquitectura Modular de Features:** Cada práctica ITIL implementa su vista en `src/features/<modulo>/` consumiendo el cascarón compartido `src/components/layout/ServiceDeskLayout.tsx`. Nunca dupliques el `Sidebar` o `Header`.
5. **Evidencias y Capturas de Figma:** Guarda las capturas de diseño en `frontend/docs/<modulo>/` usando nombres en minúsculas y kebab-case (sin acentos, espacios ni caracteres especiales). No coloques código ni proyectos anidados en `frontend/docs/`.

---

## ✍️ Microcopy y Redacción de la Interfaz

Las palabras en la interfaz deben orientar al usuario y reducir la fricción cognitiva:

1. **Botones de Acción (CTAs):**
   - Usa voz activa indicando exactamente lo que ocurrirá:
     - ❌ *Evitar:* `Enviar`, `Aceptar`, `Submit`, `OK`
     - ✅ *Usar:* `Guardar Cambios`, `Crear Petición`, `Escalar a Nivel 2`, `Activar Cuenta`, `Cerrar Ticket`
2. **Consistencia de Acciones:**
   - Si un botón dice `Escalar a Nivel 2`, el mensaje de confirmación/toast debe decir exactamente `Ticket escalado a Nivel 2`.
3. **Longitud de Línea (< 80 caracteres):**
   - Para artículos de la Base de Conocimiento (KB), soluciones de problemas y descripciones de tickets, limita el ancho del contenedor (`max-w-prose` o `max-w-2xl`) para maximizar la comodidad de lectura.

---

## 🛡️ Estados de la Interfaz (Carga, Vacío y Error)

Todo componente o tabla que maneje datos asíncronos DEBE contemplar 3 estados:

1. **Estado de Carga (Loading):**
   - Muestra skeletons (`animate-pulse`) o spinners sutiles mientras la promesa se resuelve.
2. **Estado Vacío (Empty State) como Invitación:**
   - Una pantalla sin datos no debe ser solo un texto gris pasivo. Debe orientar e invitar a la acción:
     ```tsx
     <Card className="flex flex-col items-center justify-center p-8 text-center">
       <Inbox className="h-10 w-10 text-slate-400 mb-2" />
       <h4 className="text-base font-semibold text-slate-800">No hay peticiones pendientes</h4>
       <p className="text-sm text-slate-500 mb-4">¿Necesitas solicitar equipo, accesos o software?</p>
       <Button variant="primary" onClick={() => onNuevaPeticion()}>Nueva Petición</Button>
     </Card>
     ```
3. **Estado de Error Resolutivo:**
   - Explica en lenguaje claro qué ocurrió y proporciona un camino de solución inmediato (botón de reintento):
     ```tsx
     <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
       <p className="font-medium">No se pudo cargar el monitor de eventos.</p>
       <p className="text-xs text-red-600 mt-1">Verifica tu conexión con el microservicio.</p>
       <Button variant="outline" size="sm" className="mt-3" onClick={() => recargar()}>Reintentar</Button>
     </div>
     ```

---

## ♿ Accesibilidad y Estándares Web Modernos (WCAG 2.1 AA)

1. **IDs Dinámicos y Accesibles (`useId`):**
   - En formularios y modales, genera IDs únicos con el hook nativo de React para vincular etiquetas y descripciones de error:
     ```tsx
     import { useId } from 'react';
     const id = useId();
     const errorId = useId();
     
     <label htmlFor={id}>Correo corporativo</label>
     <input id={id} type="email" autoComplete="email" aria-describedby={hasError ? errorId : undefined} />
     {hasError && <p id={errorId} role="alert">Escribe un correo válido</p>}
     ```
2. **Modales Accesibles:**
   - Deben incluir `role="dialog"`, `aria-modal="true"`, cerrarse con la tecla `Escape`, y bloquear el scroll del fondo (`overflow-hidden`).
3. **Tablas Responsivas:**
   - En pantallas pequeñas, nunca permitas que una tabla desborde el layout. Envuelve la tabla en un contenedor horizontal:
     ```tsx
     <div className="w-full overflow-x-auto rounded-xl border border-slate-200">
       <table className="w-full min-w-[640px] text-left text-sm">...</table>
     </div>
     ```

