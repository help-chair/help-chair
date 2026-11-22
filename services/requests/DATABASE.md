
# Base de datos de Requests

El servicio de Peticiones utilizará PostgreSQL como base de datos principal.

Cada servicio de Help Chair maneja su propia base de datos, por lo que Requests no comparte directamente sus tablas con otros departamentos.

## Configuración

La conexión se realiza mediante la variable de entorno `DATABASE_URL`.

Para trabajar en local también se puede utilizar SQLite cuando no esté configurada esa variable.

La configuración de PostgreSQL para desarrollo local está contemplada en `platform/deploy/local/compose.yaml`, con el servicio `requests-db`.

## Pendientes

- Comprobar la conexión con PostgreSQL.
- Ejecutar las migraciones de Django.
- Verificar que las pruebas funcionen utilizando PostgreSQL.
