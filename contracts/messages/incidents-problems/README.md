# Propuesta de intercambio Incidencias → Problemas (#36)

Estado: **propuesta v1 del payload, sin aprobación ni emisor/consumidor operativo
acreditados**. `version: 1` identifica la primera forma propuesta, no un contrato
congelado. Revisión necesaria de Incidencias, Problemas y los CODEOWNERS de
`contracts/messages` (@DonitaCosmica y @decko67); seguridad/transporte con Plataforma.
La issue no tiene criterios específicos ni milestone: relacionarla con fase 3 es
planificación inferida, no una asignación oficial. ITIL orienta la práctica, sin
imponer este mensaje ni campos.

## Fuentes y decisiones

Base de lectura: develop `d68f6592a75cfef639061f6bc8c377a5b76768a1`.
El [sobre común](../event-envelope.json) se reutiliza por `$ref`, sin modificarlo.
La dirección asíncrona Incidencias → Problemas está descrita en
[ARCHITECTURE §5](../../../docs/ARCHITECTURE.md).
[ADR-87](../../../docs/ADR-87-INFRAESTRUCTURA.md) conserva estado de propuesta;
el [Compose](../../../platform/deploy/local/compose.yaml) ya selecciona NATS
con JetStream (sin volumen en local). Esto no prueba ejecución ni entrega durable
ante pérdida del contenedor. Se propone subject `incidents.incident.observed`,
siguiendo `<origin>.<type>` del sobre; no hay configuración de ese subject aquí.
REST queda para consultas puntuales por contrato, sin nueva ruta de ingesta.

| Dato | Fuente actual | Decisión de este perfil (propuesta) |
|---|---|---|
| `id`, `origin`, `type`, `version` | Sobre común: ID UUID de outbox, servicio y versión | `incident.observed`, origen `incidents`, versión 1; UUID canónico en minúsculas |
| `payload.incident_ref` | [Incident.id](../../incidents/openapi.yaml), entero; [modelo](../../../services/incidents/incidents/models.py) con BigAutoField en settings | Decimal positivo canónico en texto, hasta int64; no `code` legible ni UUID. Cabe en referencia Problems de 64 caracteres |
| `payload.created_at` | Incident.created_at, alta persistida | Copia UTC con `Z`; no se infiere hora real de la interrupción |
| `occurred_at` | Sobre: fecha del hecho | En este tipo el hecho es el registro del incidente, igual a created_at |
| `timestamp` | Sobre: publicación | Primera publicación, UTC con `Z`, igual o posterior al alta; permanece al reintentar |
| `payload.affected_service` | Incident.affected_service, referencia de Eventos de hasta 100 caracteres, permite vacío | Exigir no vacío y sin espacios exteriores; conservar identidad exacta y mayúsculas. Retener para enriquecimiento si falta, sin inventar un servicio |
| `payload.source_event_id` | Incident.source_event_id, texto hasta 64, permite vacío | Opcional: omitir vacío, no asumir UUID ni usarlo para contar incidentes |
| `payload.company_ref` | No existe en Incident v0; arquitectura de stack por empresa | Evolución aislada del adaptador emisor: referencia opaca hasta 64 caracteres desde aprovisionamiento confiable. Falta acordar nombre/fuente concreta y vinculación autenticada al stack |
| `correlation_id` | Sobre común | UUID canónico opcional o null; trazabilidad, sin usarlo como identidad |

[Contrato de Incidencias](../../incidents/openapi.yaml) y modelo actuales no
exponen categoría ni código de error. Este v1 mínimo solo ofrece servicio como
dimensión candidata: no afirma que todos los incidentes del servicio tengan la
misma causa. Para #38 se propone una evolución separada con taxonomía/categoría y
código de error y sus fuentes acordadas, revisión de productor/consumidor y versión
incompatible nueva si se hacen obligatorios. No derivarlos del título, prioridad,
descripción, categoría de Events ni `occurrence_count` sin acuerdo. #38 debe
resolver suficiencia del patrón y población elegible antes de activar el detector.

No se transmiten personas, texto libre, credenciales ni datos crudos del evento.
[Problemas](../../problems/openapi.yaml) conserva PK int64 y referencias externas
de texto; no se cambia su modelo ni se consulta/importa la BD de otro servicio.
El ejemplo [observed.json](examples/observed.json) contiene solo datos sintéticos
de dominio, no configuración de runtime.

## Consumo propuesto y límites de garantía

1. Autenticar productor y canal del stack; comprobar que la empresa autorizada
   coincide con `payload.company_ref` antes de persistir o contar. La estructura
   no autentica `origin` ni empresa. No se acreditan ACL, firmas, JWT, scopes o
   credenciales de broker; mecanismo concreto y pruebas de aislamiento pendientes.
   D-29 de [DECISIONS](../../../docs/DECISIONS.md) tampoco prueba autenticación
   de mensajería. Un subject o una referencia en el payload no concede permiso.
2. Validar perfil y semántica. Campos desconocidos se rechazan en esta comprobación
   estricta; el sobre tiene `additionalProperties: false` aunque su prosa recomienda
   ignorarlos. No se cambia esa discrepancia compartida. Ampliaciones se revisan
   explícitamente y no se aceptan silenciosamente.
3. Identidad del mensaje: UUID `id` de outbox, registro consumidor duradero por
   (empresa autorizada, productor, id). Reintento conserva TODO el mensaje, incluida
   timestamp; hora de entrega/reintento es metadato de transporte, fuera del sobre.
   Mismo id y contenido: duplicado sin efecto. Mismo id con contenido diferente:
   conflicto, retener y alertar sin sobrescribir ni contar.
4. Identidad del incidente: (empresa autorizada, incident_ref). Nuevo id de mensaje
   para el mismo incidente no suma otro incidente. Si su payload inmutable difiere
   (incluso fuente/servicio), retener conflicto para resolución explícita: este tipo
   no define actualizaciones. Incidente distinto puede compartir source_event_id;
   el contador de Events no demuestra varios incidentes. Un mensaje tardío conserva
   created_at como fecha candidata a ventana T; no se cuenta por fecha de reentrega.
5. Propuesta futura: persistir observación y marca de procesado atómicamente antes
   del ACK. Fallo transitorio: NAK/reintento limitado con backoff; inválido, empresa
   ajena o conflicto: retención segura para revisión, sin bucle infinito. Límites,
   backoff, retención, stream/consumer/ACK y recuperación ante caída requieren
   acuerdo con Plataforma; no se configura ni prueba ninguno en este paquete.

`delivery_relation` compara dos observaciones ya válidas como referencia ejecutable
de esas reglas; no almacena mensajes, no autentica, no deduplica entre procesos y
no implementa DB/ingestor/detector. Mensajes de empresas distintas devuelven
`different-incident`: esto clasifica identidad, **no autoriza su admisión**.
#38 decidirá agrupación, N/T, frecuencia, estados elegibles, tardíos y retención;
#41 creación/vínculo y concurrencia. No se fijan umbrales ni se ejecutan esas issues.

## Validación reproducible offline

Python 3.12 y `jsonschema` 4.26.0 (incluye `referencing`), reutilizando la herramienta
ya usada en contratos de KB. Preparación opcional en entorno temporal, sin Django,
BD, variables privadas, `.env`, instalaciones globales ni cambios de locks:

```bash
uv run --offline --no-project --with jsonschema==4.26.0 python contracts/messages/incidents-problems/validate.py contracts/messages/incidents-problems/examples/observed.json
uv run --offline --no-project --with jsonschema==4.26.0 python -m unittest discover -s contracts/messages/incidents-problems -p 'test_*.py' -v
```

Requiere paquetes previamente disponibles en caché (o preparar el entorno aparte).
La validación resuelve únicamente el sobre local mediante registro explícito;
no descarga `$ref` ni el metaschema. FormatChecker verifica UUID y un comprobador
local de fechas evita depender de extras opcionales de jsonschema. Se propone
UTC con `T` y `Z` mayúsculas y hasta seis decimales (precisión de Django/Python);
segundos intercalares y precisión mayor se rechazan con diagnóstico saneado,
sin truncarlos. El schema
valida estructura, tipo/origen/versión, límites y campos; código separado comprueba
rango int64, espacios exteriores, igualdad temporal y orden de publicación. No
comprueba reloj real, igualdad con la BD original, identidad empresarial o permisos.
Errores muestran reglas/rutas del schema confiable, nunca valores ni claves del
payload; JSON ilegible, duplicado o no finito falla con diagnóstico saneado.

Las pruebas incluyen ejemplo mínimo y completo, fronteras y negativos por mutación,
compatibilidad con el sobre, rechazo de event.routed, fechas, reintentos y conflictos,
resolución offline y privacidad de errores. No acreditan broker, emisor, transacción,
deduplicación persistente, ACK, seguridad desplegada ni integración real aprobada.
