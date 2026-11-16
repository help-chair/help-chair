# 🪑 Help Chair - Dashboard de Incidentes (v1.0)

Bienvenido al repositorio de la primera versión del Frontend para el sistema Help Chair. Este proyecto es un Help Desk diseñado para la gestión, categorización y resolución eficiente de incidentes escolares, alineado con buenas prácticas de servicio.

## 🚀 Novedades de la Versión 1.0

Esta primera entrega incluye el diseño completo y funcional del **Dashboard Principal de Incidentes** y el flujo de **Apertura de Nuevos Casos**.

### 📊 Dashboard Principal (Vista General)
La pantalla principal ha sido diseñada para dar a los agentes de soporte una visión clara y rápida del estado del sistema:

*   **Menú de Navegación Lateral (Sidebar):** Estructura preparada para escalar, con accesos a Incidentes, Peticiones, Problemas, SLA y Reportes.
*   **Tarjetas de Métricas (KPIs):** Cuatro indicadores clave en la parte superior para monitoreo en tiempo real:
    *   Tickets Abiertos
    *   Tickets Cerrados
    *   Tickets Urgentes
    *   Tickets Escalados
*   **Filtros Rápidos:** Capacidad de filtrar la vista de la tabla por "Estado" y "Prioridad".
*   **Tabla de Gestión de Incidentes:** Una vista de lista detallada que incluye:
    *   Identificador único (ID) y datos del solicitante.
    *   Canal de ingreso de la falla (Email, Teléfono).
    *   **Categorización Visual:** Uso de etiquetas (badges) con colores específicos (Ej. *Excepción* en rojo, *Advertencia* en amarillo, *Petición* en morado).
    *   **Priorización:** Indicadores claros de nivel de urgencia (Urgente, Media, Baja).
    *   **Estado Actual:** Etiquetas dinámicas para tickets Abiertos (azul) y Cerrados (verde).
    *   **Acciones Directas:** Botones integrados en cada fila para "Escalar" de nivel o "Cerrar" el ticket rápidamente.
*   **Panel de Notificaciones de Escalamiento:** Un módulo lateral dedicado que alerta al equipo sobre incidentes que han pasado a Nivel 2, indicando explícitamente cuándo se debe llamar a alguien de mayor cargo.

### 🎫 Módulo de Nuevo Ticket
Un modal limpio y centrado para la captura rápida de nuevos reportes de falla, que garantiza que no falte información crucial:

*   **Identificación del Usuario:** Campos para el ID y el Nombre completo del solicitante.
*   **Canal y Descripción:** Captura del medio por el cual llegó el reporte y un área de texto para detallar la falla.
*   **Matriz de Clasificación:** Selectores integrados para definir la **Urgencia**, el **Impacto** y la **Prioridad** del caso desde el primer momento.
*   **Carga de Evidencia:** Una zona de "Drag & Drop" (arrastrar y soltar) fácil de usar para adjuntar capturas de pantalla, archivos log o PDFs que ayuden a la resolución.

## 🛠️ Notas de Diseño
*   **Estilo:** Interfaz moderna y limpia basada en fondos oscuros para el menú y tarjetas blancas para el contenido, maximizando la legibilidad.
*   **Estandarización:** Uso de un sistema de diseño consistente con bordes redondeados, botones de acción claros (primarios y secundarios) y una paleta de colores semántica para los estados.