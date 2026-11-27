# Validación local de observaciones — #38

`recurrence.validation.validate` recibe un objeto JSON ya decodificado y verifica
forma y semántica del [perfil propuesto v1 de #36](../../../contracts/messages/incidents-problems/README.md).
Devuelve `(payload, occurred_at, timestamp)` con fechas conscientes UTC, sin mutar
la entrada; `payload` conserva la referencia original, no es una copia congelada.
Los errores son `ObservationError` locales con diagnósticos fijos sin valores;
esta unidad no define respuestas HTTP.

Se exigen UUID canónicos, versión 1 (también 1.0, nunca bool), referencias opacas,
incidente decimal positivo ASCII int64, servicio informado sin espacios exteriores,
UTC con Z y hasta seis decimales, alta igual a occurred_at y publicación posterior
o simultánea. Se rechazan campos extra. El guardia NUL es deliberadamente más
estricto que el schema actual de #36: PostgreSQL text no admite NUL; las pruebas
registran esa diferencia sin modificar el contrato. No se normalizan identidades.

`utc_timestamp` interpreta fechas del perfil. `reference` verifica una referencia
opaca de hasta 64 caracteres sin espacios ni NUL; no acredita su procedencia.
`aware_utc` exige datetime consciente con offset cero: no obtiene ni autentica
received_at. El llamador debe decodificar JSON de forma estricta (duplicados y
NaN requieren tratamiento antes de esta función); aquí no hay parser de transporte.

Validar no autentica firma, canal, empresa ni productor. #36 exige company_ref
enriquecida y servicio no vacío; Incidencias actual carece del primer dato y admite
servicio vacío. No se acredita un emisor operativo ni aprobación del perfil.

Esta extracción del aporte local #38 conserva sus helpers; la ingesta futura los
importará sin duplicarlos y deberá aportar contexto confiable de empresa/productor,
transacción SQL, deduplicación, locks y pruebas de carreras. Aquí no se calculan
digests, ni se almacena, admite, confirma ACK o cuenta una observación; tampoco
se implementan broker, RLS, detector N/T, creación de problemas o integración real.
Ejecutar `make lint` y `make test` con entorno privado explícito y PostgreSQL aislado,
según el [README del servicio](../README.md); sin .env ni SQLite. Las pruebas
contrastan el ejemplo canónico y mutaciones con el validador offline de #36.
