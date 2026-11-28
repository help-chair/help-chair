
# Pruebas del servicio de Peticiones

## Objetivo

Registrar las pruebas realizadas y las verificaciones pendientes del servicio de Peticiones de Help Chair.

## Pruebas automáticas

En el PR #253 se ejecutó el workflow Requests CI de GitHub Actions.

Resultado observado:
- PR title / semantic-title: correcto.
- Requests CI / test-and-contract: correcto.
- Total: 2 checks exitosos.

Estos resultados corresponden a la ejecución de GitHub Actions. No representan una prueba de despliegue real.

## Pruebas incluidas en el servicio

El proyecto contiene los siguientes archivos:

- tests/test_peticiones.py: modelos, estados y operaciones de las peticiones.
- tests/test_permisos.py: autenticación y permisos.
- tests/test_consumers.py: recepción de mensajes e idempotencia.
- tests/test_contratos.py: validación de OpenAPI.
- tests/test_integracion_fase3.py: pruebas del flujo de Fase 3.
- tests/test_health.py: disponibilidad del servicio.

## Ejecución local

Desde services/requests, con las dependencias instaladas:

    pytest
    ruff check .
    ruff format --check
    python manage.py makemigrations --check --dry-run

Estos comandos también forman parte de las verificaciones del workflow, según su configuración.

## Pendientes de integración

- Probar la autenticación con el servicio real de Accesos.
- Comprobar la comunicación entre Backend y Frontend.
- Verificar recepción de mensajes desde NATS.
- Validar la conexión con PostgreSQL durante el despliegue.
- Registrar las pruebas funcionales del entorno testing.

## Referencias

- PR #253: integración de Fase 3.
- PR #305: correcciones de Fase 3.
- PR #306: contratos de mensajes.

Las pruebas de integración con servicios desplegados se documentarán cuando estén disponibles.
