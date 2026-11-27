# Esquema de observaciones de recurrencia — #38

Propuesta parcial: añade dos tablas PostgreSQL locales y su migración inicial.
Preparar almacenamiento no activa ingesta, deduplicación de negocio ni detector.
El [perfil #36](../../../contracts/messages/incidents-problems/README.md) integrado
no acredita acuerdo del equipo sobre este modelo ni integración autenticada real.

## Datos y garantías SQL

- `IncidentObservation`: empresa, referencia externa de incidente, servicio,
  fecha del alta, primera recepción prevista y digest del payload.
  Unicidad `(company_ref, incident_ref)` e índice `(company_ref, occurred_at)`.
- `ProcessedObservation`: empresa, productor, UUID de mensaje, digest del mensaje
  y recepción prevista. Unicidad `(company_ref, producer, message_id)`.
- Claves locales `BigAutoField`; referencias externas de texto, sin FK ni acceso
  a bases ajenas. No modifica modelos, migraciones o administración de Problemas.
- Campos no nulos; referencias de empresa hasta 64 caracteres, incidente hasta
  19, servicio hasta 100, productor hasta 32 y digests hasta 64.
- Fechas explícitas, sin reloj automático; pruebas verifican persistencia UTC.
  Restricciones únicas impiden duplicar identidades, sin sobrescribir otra fila.

## Límites y confianza

El ORM directo no constituye ingesta validada. El esquema no comprueba formato
decimal positivo/int64 de incidente, productor permitido, empresa autorizada,
formato hexadecimal/SHA256, cálculo canónico de digests ni cronología de fechas.
Tampoco preserva por sí solo la primera recepción frente a actualizaciones.
Empresa y productor requieren contexto confiable del futuro llamador; columnas
separadas y unicidad compuesta no autentican origen ni aportan aislamiento RLS.
No almacena JSON crudo; los digests previstos no autentican ni anonimizan datos.
Las representaciones textuales solo incluyen claves locales; esto no garantiza
confidencialidad de consultas, trazas o logs externos. Proteger BD y respaldos.

Una transacción del llamador puede revertir ambas tablas. No se incluye adaptador
que las escriba atómicamente, advisory lock, detección de conflictos de contenido,
ACK, broker, reintentos, retención/purga, scheduler, política ni parámetros N/T.
No crea problemas ni vínculos (#41), no añade endpoints ni modifica contratos.

## Operación y verificación

Usar el [entorno real del servicio](../README.md), PostgreSQL propio y `make migrate`;
sin `.env` automático, secretos versionados ni SQLite. No hay variables nuevas.
Revertir `recurrence` a `zero` elimina ambas tablas y sus datos: respaldar antes;
futuras migraciones dependientes requieren evaluar su reversión conjuntamente.
`make test` verifica unicidades, identidades independientes, persistencia,
rollback y representaciones sobre PostgreSQL; no acredita deduplicación durable,
autenticación, ingesta real o la aceptación completa de #38.
