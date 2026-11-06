# Mapeo ITIL v4 / ITIL v4 Mapping

## 🇪🇸 Español

ITIL v4 organiza el trabajo en **prácticas** dentro del Sistema de Valor del Servicio (SVS). Help Chair las implementa así:

| Práctica ITIL v4 | Servicio Help Chair | Equipo | Carpeta | Notas |
|---|---|---|---|---|
| Monitoring and Event Management | Eventos | 1 | `services/events` | Tipos: informativo, advertencia, excepción. |
| Service Request Management | Peticiones | 3 | `services/requests` | Absorbe "cambios" en el MVP. |
| Incident Management | Incidencias | 4 | `services/incidents` | Prioridad = impacto × urgencia. |
| Problem Management | Problemas | 5 | `services/problems` | Incluye base de errores conocidos. |
| Knowledge Management | Base de Conocimiento | 5 | `services/knowledge` | Consumida por API. |
| Service Desk | Frontend | 6 | `frontend` | Punto único de contacto. |
| Information Security Management / acceso (dentro de Service Request Mgmt) | Accesos | 2 | `services/access` | ITIL v4 no tiene "Access Management" como práctica independiente. |
| Service Level Management | Configuración de SLA | 1 (propuesto) | `services/events` | Definido en el onboarding. |
| Service Catalogue Management | Catálogo de servicios | 1 (propuesto) | `services/events` | Servicios + importancia definidos por la empresa. |
| Change Enablement | *Fase 2* | — | — | Diferido; en el MVP lo cubre Peticiones. |
| Deployment Management / Infrastructure & Platform Mgmt | Plataforma | 7 | `platform/*` | Habilitación técnica del propio producto. |

**Regla del proyecto:** todo término de dominio (estados, prioridades, tipos) debe usar el vocabulario ITIL v4. Si un equipo duda, consulta este documento y abre un issue en este repositorio.

## 🇬🇧 English

ITIL v4 organises work into **practices** within the Service Value System (SVS). Help Chair implements them as follows:

| ITIL v4 practice | Help Chair service | Team | Folder | Notes |
|---|---|---|---|---|
| Monitoring and Event Management | Events | 1 | `services/events` | Types: informational, warning, exception. |
| Service Request Management | Requests | 3 | `services/requests` | Absorbs "changes" in the MVP. |
| Incident Management | Incidents | 4 | `services/incidents` | Priority = impact × urgency. |
| Problem Management | Problems | 5 | `services/problems` | Includes known-error database. |
| Knowledge Management | Knowledge Base | 5 | `services/knowledge` | Consumed via API. |
| Service Desk | Frontend | 6 | `frontend` | Single point of contact. |
| Information Security Management / access (within Service Request Mgmt) | Access | 2 | `services/access` | ITIL v4 has no standalone "Access Management" practice. |
| Service Level Management | SLA configuration | 1 (proposed) | `services/events` | Defined during onboarding. |
| Service Catalogue Management | Service catalogue | 1 (proposed) | `services/events` | Services + importance defined by the company. |
| Change Enablement | *Phase 2* | — | — | Deferred; Requests covers it in the MVP. |
| Deployment Management / Infrastructure & Platform Mgmt | Platform | 7 | `platform/*` | Technical enablement of the product itself. |

**Project rule:** every domain term (states, priorities, types) must use ITIL v4 vocabulary. If in doubt, check this document and open an issue in this repository.
