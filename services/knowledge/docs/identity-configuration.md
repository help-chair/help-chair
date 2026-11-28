# Preparación del contexto de identidad — #255

`config.environment.identity_config()` valida y devuelve el contexto fijo del
futuro integrador JWT. Las variables siguientes son obligatorias **al invocarlo**;
el arranque actual no llama a este helper ni añade requisitos al proceso.

| Nombre | Propósito y formato |
|---|---|
| JWKS_URL | Destino HTTP(S) confiable con host y puerto válido, terminado en `/.well-known/jwks.json` |
| JWT_ISSUER | Emisor esperado del token, texto no vacío |
| EMPRESA_ID | Empresa fija del stack, texto no vacío |

El destino no admite credenciales, espacios, query ni fragmento. El helper exige
valores explícitos del entorno del proceso: sin defaults, `.env` automático ni
fallback. Ausencia, vacío o formato inválido produce `ImproperlyConfigured` con
el nombre de la variable, sin su valor. El operador debe proteger el destino y
su contexto; el solicitante y las cabeceras JWT no deben elegirlos.

El resultado tiene claves `url`, `issuer` y `company`. No descarga JWKS ni modifica
ajustes Django/DRF, Compose, logging, rutas, errores HTTP o permisos. El inventario
`.env.example` conserva asignaciones vacías; no copiarlo ni cargarlo para ejecutar.
La política provisional del CRUD ya integrado no se corrige en este incremento;
la activación futura deberá conciliar autenticación, autorización, visibilidad,
autoría y errores con esa API. No acredita identidad global activa ni acuerdos.

Con entorno privado real y PostgreSQL aislado suministrados, ejecutar `make lint`
y `make test` desde el servicio. Las pruebas usan contexto de ensayo explícito y
comprueban entradas inválidas, ausencia y errores sin valores. También se adapta
la aserción JWT de PR #297 al handler `{codigo, detalle}` ya integrado por #296,
sin modificar ese handler o el comportamiento HTTP. #255 sigue incompleta.
