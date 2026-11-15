# Sistema de Diseño y Evidencia UI/UX · Help Chair

> Documentación oficial del Sistema de Diseño, guía para Figma y justificación de ingeniería para el **Service Desk (ITIL v4)** de Help Chair.

---

## 🔗 Enlace al Proyecto en Figma

* **Archivo Maestro en Figma:** [Ver archivo en Figma](https://www.figma.com/design/o3232M6n3YJk5PWdPbK6EM/Help-Chair-%C2%B7-Service-Desk--Design-System---Templates-?node-id=2-400&t=FJ537GG11wCmIZYz-1)
* **Modo de Acceso:** Lectura / Comentarios para evaluadores académicos.
* **Prototipo Interactivo:** [Probar Prototipo en Vivo](https://www.figma.com/proto/o3232M6n3YJk5PWdPbK6EM/Help-Chair-%C2%B7-Service-Desk--Design-System---Templates-?node-id=2-924&p=f&t=qJuO3gYh3QvtkAEm-1&scaling=min-zoom&content-scaling=fixed&page-id=2%3A400)

---

## 🎓 Justificación Académica y Teórica (ITSM / ITIL v4)

Este sistema de diseño fue concebido bajo los principios de la **Gestión de Servicios de Tecnologías de la Información (GSTI)** y la biblioteca **ITIL v4**:

1. **Service Desk como Punto Único de Contacto (SPOC):**
   * Toda la interacción de los usuarios y agentes converge en una única interfaz unificada (Single Page Application). La interfaz actúa como el *gateway* hacia los microservicios de Eventos, Incidencias, Peticiones y Problemas.
2. **Semántica de Colores Operacionales (Monitoreo de Eventos):**
   * En lugar de emplear colores estéticos arbitrarios, la paleta codifica el estado operacional según la práctica *Monitoring and Event Management*:
     * **Informativo (Azul #2563eb):** Eventos normales de rutina (backups, inicio de sesión, tareas de mantenimiento programadas).
     * **Advertencia (Ámbar #d97706):** Umbrales alcanzados (disco > 80%, latencia elevada, SLAs con menos del 20% de tiempo restante). Requiere vigilancia preventiva.
     * **Excepción (Rojo #dc2626):** Fallos críticos, degradación severa de servicio o incidentes de alta prioridad (P1/P2).
     * **Éxito / Normalidad (Verde #16a34a):** Servicios operativos, tickets resueltos y metas de SLA cumplidas.
     * **Petición Estándar (Violeta #7c3aed):** Trámites del catálogo de servicios que requieren aprobación sin representar una falla.
3. **Ergonomía Visual y Accesibilidad (WCAG 2.1 Nivel AA):**
   * Contraste mínimo de 4.5:1 en textos principales.
   * Uso redundante de información: ningún estado crítico se comunica **únicamente** con color; siempre se acompaña de texto descriptivo e iconografía de soporte (*Lucide Icons*).
   * Reducción de fatiga cognitiva: jerarquía limpia basada en tarjetas (*Cards*) con espaciados múltiplos de 4 y 8 píxeles.

---

## 📑 Estructura de Páginas en Figma

El archivo de Figma está organizado en 7 páginas modulares para permitir el trabajo en paralelo de los diferentes equipos de gestión:

```
📁 Help Chair Figma
├── 🎨 00. Tokens de Diseño & UI Kit
├── 📊 01. Dashboard & Gateway (Eventos)
├── 🚨 02. Gestión de Incidencias
├── 📥 03. Gestión de Peticiones
├── 🛡️ 04. Gestión de Problemas & KB
├── 🔐 05. Gestión de Accesos & Onboarding
└── 📱 06. Prototipo Interactivo Global
```

---

### Página 00: `🎨 Tokens de Diseño & UI Kit`
**Propósito:** Definir los cimientos visuales que todos los equipos deben reutilizar.

* **Paleta de Colores (Color Styles):**
  * `Brand/Primary`: Indigo 600 (`#4f46e5`), Primary Hover (`#6366f1`).
  * `Neutrals`: Slate 900 (`#0f172a`), Slate 800 (`#1e293b`), Slate 100 (`#f1f5f9`), Slate 50 (`#f8fafc`).
  * `ITIL States`: Info (`#2563eb`), Warning (`#d97706`), Exception (`#dc2626`), Success (`#16a34a`), Request (`#7c3aed`).
* **Tipografía (Text Styles):**
  * `Heading 1 / Page Title`: Inter Bold, 24px, Line Height 32px.
  * `Heading 2 / Section Title`: Inter SemiBold, 18px, Line Height 24px.
  * `Heading 3 / Card Title`: Inter SemiBold, 16px, Line Height 20px.
  * `Body / Regular Text`: Inter Regular, 14px, Line Height 20px.
  * `Caption / Badges & Metadatos`: Inter Medium, 12px, Line Height 16px.
* **Componentes Maestros con Variantes:**
  * **Master Layout (Shell):** Sidebar oscuro fijo (`w-64`, `bg-slate-900`) + Header blanco (`h-16`).
  * **Button:** Variantes `Primary`, `Secondary`, `Outline`, `Danger`, `Ghost` en tamaños `sm`, `md`, `lg`.
  * **Badge:** Variantes `Info`, `Warning`, `Exception`, `Success`, `Request`, `Outline`.
  * **Card Container:** Variantes `Default`, `Interactive/Hover`, `Metric KPI`.
  * **Form Controls:** Inputs de texto, selectores desplegables, textareas y checkboxes con estados *Default*, *Focus*, *Error*.

---

### Página 01: `📊 Dashboard & Gateway (Gestión de Eventos)`
**Responsable:** Equipo 1 (Eventos) & Equipo 6 (Frontend).  
**Propósito:** Servir como centro de operaciones y vista inicial del Service Desk.

* **Elementos a diseñar:**
  1. **Barra de Contexto de Empresa (Multi-tenant Header):**
     * Indicador del subdominio de la empresa (`{empresa}.helpchair.example`).
     * Selector de perfil de usuario activo (ej. *Service Desk Lead*).
  2. **Tarjetas de KPIs Operacionales (Fila superior):**
     * *Eventos (24h):* Total de eventos y porcentaje auto-enrutados.
     * *Incidencias Abiertas:* Contador con indicador de incidencias críticas (P1).
     * *Peticiones en Trámite:* Total de solicitudes activas y pendientes de aprobación.
     * *Cumplimiento de SLA:* Porcentaje global de cumplimiento mensual (meta 95%).
  3. **Monitor de Eventos en Tiempo Real (Live Feed):**
     * Tabla dinámica con columnas: ID del evento, Hora/Timestamp, Tipo ITIL (Badge), Descripción, Componente de Origen, Destino asignado y Estado del procesamiento.
     * Filtro interactivo por severidad (*Todos*, *Informativos*, *Advertencias*, *Excepciones*).
  4. **Panel de Enrutamiento y Acciones Rápidas:**
     * Botón CTA para registro manual de evento o ticket.
     * Acceso directo con badges contadores hacia Incidencias, Peticiones y Problemas.

---

### Página 02: `🚨 Gestión de Incidencias`
**Responsable:** Equipo 4.  
**Práctica ITIL:** *Incident Management* (Restaura la operación normal del servicio lo más rápido posible).

* **Elementos a diseñar:**
  1. **Matriz de Prioridad Dinámica:**
     * Selector de **Impacto** (Alto, Medio, Bajo) × **Urgencia** (Alta, Media, Baja) = Cálculo automático de **Prioridad** (P1-Crítica, P2-Alta, P3-Media, P4-Baja).
  2. **Vista de Incidentes (Lista y Tablero Kanban):**
     * Columnas por estado ITIL: *Nuevo*, *Asignado*, *En Proceso*, *En Espera*, *Resuelto*, *Cerrado*.
  3. **Detalle del Incidente:**
     * Cronómetro regresivo de SLA (Tiempo restante para resolución antes del incumplimiento).
     * Historial de auditoría / Bitácora de acciones del agente.
     * Botón para asociar el incidente a un *Problema* o buscar solución en la *Base de Conocimiento*.

---

### Página 03: `📥 Gestión de Peticiones`
**Responsable:** Equipo 3.  
**Práctica ITIL:** *Service Request Management* (Gestiona solicitudes estándar definidas en el catálogo).

* **Elementos a diseñar:**
  1. **Portal de Catálogo de Servicios (Vista de Autoservicio):**
     * Tarjetas de servicios categorizadas (ej. *Hardware*, *Software*, *Permisos y Accesos*, *Telefonía*).
     * Cada tarjeta muestra tiempo estimado de entrega (SLA) y si requiere aprobación de un líder.
  2. **Formulario de Solicitud de Servicio:**
     * Campos personalizados según el servicio seleccionado.
     * Adjuntar archivos o justificación de negocio.
  3. **Línea de Vida de la Petición:**
     * Diagrama de pasos visuales: *Enviada → Aprobación pendiente → En provisión → Completada*.

---

### Página 04: `🛡️ Gestión de Problemas & Base de Conocimiento (KB)`
**Responsable:** Equipo 5.  
**Práctica ITIL:** *Problem Management* & *Knowledge Management* (Identifica causas raíz y previene recurrencias).

* **Elementos a diseñar:**
  1. **Panel de Análisis de Problemas:**
     * Lista de problemas identificados a partir de incidencias recurrentes.
     * Vista de análisis de Causa Raíz (Diagrama de Ishikawa o registro de los 5 Porqués).
  2. **Base de Errores Conocidos (KEDB - Known Error Database):**
     * Ficha de "Workaround" (Solución temporal documentada para que los operadores del Service Desk puedan resolver incidentes mientras se repara la causa raíz).
  3. **Visor de Artículos de Conocimiento (KB):**
     * Barra de búsqueda inteligente con etiquetas.
     * Lector de artículos con botón de feedback (*¿Te resultó útil este artículo? Sí / No*).

---

### Página 05: `🔐 Gestión de Accesos & Onboarding de Empresa`
**Responsable:** Equipo 2 (Accesos) & Equipo 7 (Plataforma).  
**Práctica ITIL:** *Information Security Management* & Habilitación Técnica.

* **Elementos a diseñar:**
  1. **Pantalla de Inicio de Sesión (Login Multi-tenant):**
     * Detección del subdominio de la empresa y formulario seguro de autenticación.
  2. **Asistente de Onboarding (Primer arranque para Administradores):**
     * Paso 1: Información de la empresa y departamentos.
     * Paso 2: Configuración de catálogo de servicios iniciales.
     * Paso 3: Configuración de matriz de SLA y horarios hábiles.
     * Paso 4: Alta de usuarios y asignación de roles RBAC (Administrador, Agente N1, Agente N2, Usuario final).

---

### Página 06: `📱 Prototipo Interactivo Global`
**Propósito:** Demostración en vivo para la evaluación académica.

* **Flujos conectados con flechas de interacción (Figma Prototyping):**
  * **Flujo A (Detección a Incidente):** Clic en un evento de tipo *Excepción* en el Dashboard → Abre modal de detalle → Clic en "Escalar a Incidente" → Abre formulario con datos prellenados.
  * **Flujo B (Autoservicio):** Usuario entra al catálogo → Selecciona "Solicitar Acceso a Servidor" → Envía formulario → Se refleja en la lista de peticiones en estado *En Aprobación*.
  * **Flujo C (Consulta de KB):** Agente abre un incidente → Clic en "Consultar KB" → Visualiza solución temporal → Resuelve el ticket.

---

## 🔄 Correspondencia entre Figma y Código Fuente

Para garantizar que el código sea fiel al diseño de Figma, las propiedades se corresponden de la siguiente forma:

| Elemento en Figma | Token en CSS / Tailwind | Archivo de Código |
|---|---|---|
| Color `ITIL/Info` (`#2563eb`) | `bg-itil-info` / `text-itil-info` | `tailwind.config.js` |
| Color `ITIL/Warning` (`#d97706`) | `bg-itil-warning` / `text-itil-warning` | `tailwind.config.js` |
| Color `ITIL/Exception` (`#dc2626`) | `bg-itil-exception` / `text-itil-exception` | `tailwind.config.js` |
| Color `ITIL/Success` (`#16a34a`) | `bg-itil-success` / `text-itil-success` | `tailwind.config.js` |
| Color `ITIL/Request` (`#7c3aed`) | `bg-itil-request` / `text-itil-request` | `tailwind.config.js` |
| Radio de esquinas (8px) | `rounded-lg` / `--radius: 0.5rem` | `src/index.css` |
| Componente `Master Button` | `<Button variant="..." size="...">` | `src/components/ui/button.tsx` |
| Componente `Status Badge` | `<Badge variant="...">` | `src/components/ui/badge.tsx` |
| Componente `KPI Card` | `<Card>` | `src/components/ui/card.tsx` |

---

## 🏆 Criterios Calidad Cumplidos

Al presentar este documento y el prototipo de Figma ante el cuerpo docente, se evidencian los siguientes logros formativos:

1. **Alineación con el Marco ITIL v4:** Demostración de que la interfaz no es genérica, sino que refleja las prácticas oficiales de *Service Desk*, *Monitoring & Event Management*, *Incident Management*, *Service Request Management* y *Problem Management*.
2. **Ciclo de Vida Formal de Software:** Separación rigurosa de etapas (*Figma para Prototipado UX/UI → OpenAPI para Contratos de Microservicios → React/Tailwind con IA para Implementación*).
3. **Gobierno y Consistencia Multiequipo:** Capacidad de coordinar a 7 equipos de trabajo bajo un mismo sistema de diseño sin inconsistencias visuales.
