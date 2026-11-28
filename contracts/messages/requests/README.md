
# Contratos de mensajes de Peticiones

## Descripción

Esta carpeta contiene los contratos de los mensajes que Peticiones recibe desde Eventos mediante NATS.

Se utiliza el esquema común de `contracts/messages/event-envelope.json` para mantener el mismo formato de comunicación entre los servicios.

## Mensajes recibidos

Peticiones recibe mensajes `event.routed` publicados por Eventos mediante el subject:

`events.routed.requests`

Actualmente se contemplan dos reglas:

- R5: solicitudes relacionadas con el catálogo de servicios.
- R8: solicitudes relacionadas con cambios.

Ambas utilizan el destino `REQUESTS`.

## Estructura

Los mensajes incluyen un identificador, tipo, versión, servicio de origen, fechas y un payload con la información correspondiente.

El campo `id` permite identificar mensajes repetidos y evitar procesarlos más de una vez.

## Archivos

- `event-routed.requests.v1.schema.json`: esquema de recepción de mensajes.
- `examples/catalog-request.json`: ejemplo de la regla R5.
- `examples/change-request.json`: ejemplo de la regla R8.
- `test_contract.py`: pruebas de validación del contrato.

## Pruebas

Las pruebas comprueban que los mensajes respeten el esquema, que el destino sea Peticiones y que cada regla tenga su categoría correspondiente.

Para ejecutarlas desde la raíz del repositorio, con las dependencias `jsonschema` y `referencing` instaladas:

`python -m unittest discover -s contracts/messages/requests -p "test_contract.py" -v`

Estas pruebas validan el contrato JSON. La recepción real mediante NATS y el control de mensajes duplicados deberán comprobarse con el servicio funcionando.

## Integración

Los contratos utilizan el formato común de Eventos y no modifican el código de otros servicios.

Cualquier cambio en los esquemas debe revisarse con los responsables de los contratos antes de integrarse a develop.
