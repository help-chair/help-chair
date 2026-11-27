# Validación explícita de identidad — #255

`core.identity.AccessAuthentication` verifica tokens de Accesos cuando una vista
lo selecciona explícitamente. Este incremento no lo registra en los ajustes DRF,
no cambia rutas, middleware, permisos de negocio ni el contrato de errores actual.
La activación, configuración operativa y matriz de permisos son entregas posteriores.

El integrador deberá suministrar `settings.ACCESS_IDENTITY` con `url` (destino JWKS
confiable), `issuer` (emisor esperado) y `company` (empresa del stack). Se consulta
solo al autenticar un Bearer; aquí no se añaden variables de entorno, valores
predeterminados ni carga de archivos de configuración. Una configuración ausente
rechaza la autenticación con el mismo mensaje genérico.

Solo se acepta RS256, firma válida, `kid` limitado y claims obligatorios de Accesos:
`sub` UUID, `exp` e `iat` enteros, `iss`, `empresa`, `rol`, `permisos` y `token_type`
de acceso. Los roles y cinco permisos corresponden al catálogo actual de Accesos;
no se inventan scopes ni identidades de servicio. No se acepta una audiencia
arbitraria. `Identity` es inmutable; los claims verificados quedan en `request.auth`.

El transporte, comprobación RSA y caché se reutilizan desde
[`core.jwks`](../core/jwks.py), integrado por PR #294. Las cabeceras no confiables
no eligen el destino de descarga; se rechazan `jku`, `jwk`, `x5u`, `crit` y `b64`.
Los errores se convierten en `AuthenticationFailed` sin datos del token o del JWKS.

Las pruebas usan claves privadas RSA y tokens efímeros en memoria, JWKS simulado
y una vista de ensayo con autenticación explícita e `IsAuthenticated`, sin
`force_authenticate`. La suite requiere el PostgreSQL aislado y entorno privado
indicados en el [README](../README.md). Esto no acredita Accesos remoto, Jenkins,
autorización de consumidores ni autenticación global habilitada en producción.
