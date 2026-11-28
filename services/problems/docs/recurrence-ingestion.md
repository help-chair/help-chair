# Registro local de observaciones — #38

`recurrence.observations.ingest(message, company_ref=..., producer=...,
received_at=...)` registra el [perfil propuesto #36](../../../contracts/messages/incidents-problems/README.md)
usando el [validador integrado](recurrence-validation.md) y PostgreSQL propio.
El llamador debe aportar empresa/productor confiables y recepción consciente UTC.
La función compara el contexto con el mensaje: no autentica firma, JWT, canal,
identidad empresarial ni correspondencia con una variable del stack.

Devuelve `accepted` al insertar observación y marca; `duplicate-message` para
el mismo ID/contenido; `same-incident` para otro ID con el mismo payload inmutable.
El reintento no cambia la primera recepción de la observación ni añade otra fila.
Las identidades son (empresa, productor, ID de mensaje) y (empresa, incidente).
Conflictos rechazan mediante `ObservationError` fijo sin sobrescribir o marcar;
no son respuestas HTTP. Se preservan valores; solo versión 1/1.0 es equivalente
al calcular el digest del mensaje, además del orden de claves JSON.

Observación y marca se escriben en una transacción. `company_lock` serializa
operaciones cooperativas de esa empresa; no es RLS ni control de acceso. Los hashes
comparan contenido: no autentican ni anonimizan. Escrituras directas ajenas a este
protocolo no obtienen sus garantías. La función no genera logs con el mensaje.
Retornar bajo un `atomic` externo no significa commit definitivo: un futuro ACK
requiere éxito del commit más externo; no se implementa transporte o confirmación.

Se exige JSON ya decodificado estrictamente por el llamador; no hay parser nuevo.
Incidencias actual no entrega company_ref y permite servicio vacío; la integración
requiere enriquecimiento confiable y acuerdos pendientes. No se acredita emisor
operativo, broker, identidad real, detector N/T, creación de problemas o vínculos.
Las futuras CLI importarán helpers de `recurrence.validation` sin duplicarlos.

Desde el servicio, con entorno privado explícito y PostgreSQL aislado según el
[README](../README.md): `make lint`, `make test` y checks Django/migraciones.
Sin .env, SQLite o secretos versionados. Las pruebas comprueban replay, conflictos,
rollback y cinco carreras con conexiones propias, y observan espera advisory hasta
commit externo mediante metadatos PostgreSQL; no acreditan Jenkins o producción.
