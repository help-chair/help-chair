# Registro de decisiones / Decision log

| ID | Decisión / Decision | Estado / Status |
|---|---|---|
| D-01 | **Monorepo** (reemplaza la decisión inicial de polyrepo, para evitar problemas de coordinación). Los servicios siguen siendo independientes: contenedor, BD y CI propios / **Monorepo** (replaces the initial polyrepo decision to avoid coordination problems). Services stay independent: own container, DB and CI | ✅ Aceptada (cambiada 4-nov-2026) |
| D-02 | Cada equipo elige su lenguaje, sujeto al contrato mínimo de servicio / Each team picks its language, subject to the minimum service contract | ✅ Aceptada |
| D-03 | Database per service; cada equipo elige su motor / Database per service; each team picks its engine | ✅ Aceptada |
| D-04 | Subdominio `{empresa}.helpchair.example` / Subdomain `{company}.helpchair.example` | ✅ Aceptada |
| D-05 | KB como servicio propio del equipo de Problemas, consumida por API / KB as its own service owned by Problems, consumed via API | ✅ Aceptada |
| D-06 | 7 equipos / 7 teams | ✅ Aceptada |
| D-07 | Broker de mensajes por stack; motor propuesto: NATS / Per-stack message broker; proposed engine: NATS | 🟡 Propuesta (motor por confirmar) |
| D-08 | Namespace de K8s por empresa + NetworkPolicy / K8s namespace per company + NetworkPolicy | 🟡 Propuesta |
| D-09 | Autenticación dentro del stack; directorio global solo mapea usuario/dominio → empresa / Authentication inside the stack; global directory only maps user/domain → company | 🟡 Propuesta |
| D-10 | Change Enablement diferido a fase 2 (lo cubre Peticiones) / Change Enablement deferred to phase 2 (covered by Requests) | 🟡 Propuesta |
| D-11 | Dueño de catálogo de servicios, matriz de prioridad y SLA: Eventos / Owner of service catalogue, priority matrix and SLAs: Events | 🟡 Propuesta |
| D-12 | Framework de frontend / Frontend framework | ⚪ Abierta |
| D-13 | Estrategia de reducción de recursos por stack / Per-stack resource reduction strategy | ⚪ Abierta |
| D-14 | Licencia del proyecto / Project license | ⚪ Abierta |
| D-15 | `CODEOWNERS` por carpeta + CI filtrado por ruta para mantener la independencia de cada equipo / Per-folder `CODEOWNERS` + path-filtered CI to keep each team independent | ✅ Aceptada |
| D-16 | Versionado por servicio con etiquetas `<carpeta>/vX.Y.Z` e imagen `ghcr.io/help-chair/hc-<servicio>` / Per-service versioning with `<folder>/vX.Y.Z` tags and image `ghcr.io/help-chair/hc-<service>` | 🟡 Propuesta |
