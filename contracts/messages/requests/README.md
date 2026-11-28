
# Contratos de mensajes de Peticiones

## Descripción

Esta carpeta contiene el contrato de los mensajes que el servicio de Peticiones recibe desde Eventos mediante NATS.

Se utiliza el esquema común definido en `contracts/messages/event-envelope.json` para mantener el mismo formato de comunicación entre los servicios de Help Chair.

## Mensajes recibidos

Por ahora se documenta el mensaje `event.routed`, publicado por Eventos cuando una solicitud debe dirigirse a Peticiones.

El mensaje utiliza el siguiente subject:

`events.routed.requests`

Para Peticiones se contempla la regla R5, correspondiente a solicitudes del catálogo de servicios.

## Estructura del mensaje

Cada mensaje contiene:

- `id`: identificador único del mensaje.
- `type`: tipo de evento recibido.
- `version`: versión del contrato.
- `origin`: servicio que publica el mensaje.
- `timestamp`: fecha de publicación.
- `occurred_at`: fecha del evento.
- `correlation_id`: identificador opcional de seguimiento.
- `payload`: información de la solicitud.

El identificador `id` permite controlar el procesamiento duplicado de mensajes.

## Archivos

- `event-routed.requests.v1.schema.json`: contrato de recepción.
- `examples/catalog-request.json`: ejemplo de una solicitud de catálogo.

## Validaciones pendientes

Se debe comprobar que el consumidor de Peticiones:

1. Reciba correctamente los mensajes desde NATS.
2. Procese únicamente los mensajes destinados a Requests.
3. Evite procesar dos veces un mismo mensaje.
4. Maneje los errores sin perder información.

Estas comprobaciones se realizarán cuando el consumidor esté integrado y disponible para las pruebas.

## Integración

Este contrato documenta la recepción de mensajes. No modifica el funcionamiento de Eventos ni agrega nuevos tipos de mensajes.

Los cambios deben revisarse con los responsables de los contratos antes de integrarse a develop.
