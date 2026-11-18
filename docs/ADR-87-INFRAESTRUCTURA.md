
# ADR-87 - Decisión de infraestructura para Help Chair

**Área:** Plataforma de Deployment  
**Issue:** #87  
**Estado:** Propuesta pendiente de aprobación

## 1. Objetivo

Definir qué servicios y herramientas podemos utilizar para desplegar Help Chair en la nube.

Como estamos desarrollando un proyecto escolar, buscamos opciones que no sean demasiado costosas, que podamos utilizar para las pruebas y que sean compatibles con las tecnologías que ya se eligieron.

## 2. Servicio en la nube

Se revisaron tres proveedores:

| Proveedor | Ventajas | Desventajas |
|---|---|---|
| Google Cloud | Ofrece créditos iniciales para cuentas nuevas elegibles y permite crear máquinas virtuales. | Es necesario verificar la cuenta, los créditos y los costos de los recursos. |
| Microsoft Azure | Cuenta con Azure for Students, que puede ser una buena opción utilizando una cuenta escolar. | Los créditos y servicios disponibles dependen de los requisitos del programa. |
| AWS | Tiene varios servicios para desplegar aplicaciones y beneficios para cuentas nuevas. | Debemos revisar sus límites y costos para no consumir los créditos rápidamente. |

**Propuesta:** utilizar Google Cloud para comenzar las pruebas. Su crédito inicial puede ayudarnos a trabajar sin pagar directamente mientras esté disponible.

Si no podemos activar una cuenta o los recursos no son suficientes, consideraríamos Azure for Students como segunda opción.

## 3. Kubernetes

Kubernetes nos permitirá administrar los contenedores de los distintos servicios de Help Chair.

Se consideraron dos opciones:

- **GKE:** Kubernetes administrado por Google Cloud. Facilita algunas tareas de administración, pero puede generar costos adicionales.
- **k3s:** versión ligera de Kubernetes que podemos instalar en una máquina virtual. Requiere que nosotros administremos el servidor.

**Propuesta:** comenzar con k3s porque queremos utilizar una infraestructura sencilla durante las primeras pruebas y evitar gastos innecesarios.

Más adelante tendríamos que comprobar si los recursos disponibles son suficientes para todos los servicios y las bases de datos.

## 4. Registro de imágenes

Las imágenes de los contenedores deben almacenarse en un registro para que después puedan utilizarse durante el despliegue.

Las opciones revisadas fueron:

- **GHCR:** registro de imágenes de GitHub. Permite relacionar las imágenes con nuestro repositorio.
- **Artifact Registry:** servicio de Google Cloud para guardar imágenes, con costos según el almacenamiento y uso.

**Propuesta:** utilizar GHCR porque ya estamos trabajando con GitHub y es una opción contemplada en el proyecto.

## 5. Broker de mensajes

El broker se utilizará para enviar mensajes entre los servicios del sistema.

Se revisaron estas alternativas:

- **NATS:** ligero y adecuado para comunicación mediante mensajes entre servicios.
- **RabbitMQ:** permite trabajar con colas de mensajes y distintas formas de distribuirlos, aunque requiere administrar su configuración.

**Propuesta:** utilizar NATS. Ya aparece como opción en las decisiones del proyecto y consideramos que puede servir para comenzar.

## 6. Costos estimados

El costo dependerá principalmente de la máquina virtual, el almacenamiento y el tráfico de red.

| Recurso | Costo |
|---|---|
| Máquina virtual | Depende del tamaño y las horas de uso |
| Almacenamiento | Depende de los GB utilizados |
| Tráfico de red | Depende de la transferencia y los servicios contratados |
| k3s | Sin licencia, pero necesita recursos del servidor |
| GHCR | Gratuito para imágenes públicas, sujeto a las condiciones de GitHub |
| NATS | Sin licencia, pero consume recursos del servidor |

Por ahora no tenemos un costo mensual definitivo porque todavía necesitamos conocer cuánta memoria y procesamiento utilizarán los servicios.

También debemos confirmar si contamos con créditos educativos activos antes de contratar o activar recursos.

## 7. Decisión propuesta

Para comenzar con el despliegue de Help Chair proponemos:

- **Nube:** Google Cloud.
- **Kubernetes:** k3s.
- **Registro de imágenes:** GHCR.
- **Broker:** NATS.

La propuesta busca que podamos comenzar las pruebas sin utilizar una infraestructura demasiado costosa.

Todavía necesitamos confirmar que podamos acceder a Google Cloud, calcular el costo mensual y revisar que las herramientas funcionen correctamente con los servicios del proyecto.

Esta decisión queda pendiente de aprobación por el equipo de Plataforma.

## 8. Fuentes consultadas

- Google Cloud: https://cloud.google.com/free
- Azure for Students: https://azure.microsoft.com/free/students/
- AWS: https://aws.amazon.com/free/
- k3s: https://docs.k3s.io/
- GitHub Container Registry: https://docs.github.com/en/packages
- NATS: https://docs.nats.io/
- RabbitMQ: https://www.rabbitmq.com/docs
