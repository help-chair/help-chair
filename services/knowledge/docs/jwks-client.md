# Cliente JWKS de Knowledge — incremento de #255

`core.jwks` extrae el transporte, validación RSA y caché del aporte local
`431127b7baa955292e4c747aba2cb59f05d679d1`, antes en `core.identity`.
No activa autenticación, rutas, ajustes, variables obligatorias ni permisos.
La dependencia PyJWT con soporte criptográfico ya procede de PR #287.

El destino debe proceder de configuración confiable validada por el futuro
integrador; nunca de cabeceras JWT, entrada del usuario o redirecciones.
Este módulo no valida la URL ni claims, emisor, empresa, rol o permisos.
El integrador deberá validar también `kid` mediante `KID` antes de consultar.
Una clave pública obtenida no acredita por sí sola la identidad del solicitante.

Transporte sin proxies del entorno ni redirecciones, timeout de socket de tres
segundos y documento máximo de 65536 bytes. El timeout no es un presupuesto total
contra respuestas lentas por fragmentos. Acepta de una a dieciséis claves RSA
RS256 de firma, públicas, con exponente 65537 y tamaños de 2048 a 8192 bits.
Rechaza identificadores duplicados, parámetros privados y operaciones distintas
de verificación. Un documento inválido se rechaza completo.

La caché por proceso conserva claves cinco minutos; un `kid` desconocido permite
refrescar como máximo una vez cada diez segundos. Un bloqueo serializa el refresco.
Un fallo no prolonga claves vencidas; las todavía vigentes conservan su plazo.
La fábrica retiene cuatro destinos como máximo; cada worker tiene estado propio.
No hay persistencia ni coordinación distribuida.

Desde el servicio, con entorno privado y PostgreSQL de ensayo suministrados:
`make lint` y `make test`. Las pruebas generan claves privadas solo en memoria,
comprueban rotación, vencimiento, concurrencia y HTTP loopback real sin Accesos.

El siguiente incremento deberá importar estas funciones desde `core.jwks` y
eliminar sus copias del borrador `identity.py` antes de publicarlo. Quedan pendientes
el validador JWT, configuración, integración DRF, matriz de roles y aceptación de
consumidores. Este incremento referencia #255; no completa esa issue.
