
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
| Google Cloud | Ofrece 300 USD de crédito inicial durante 90 días para cuentas nuevas elegibles y permite crear máquinas virtuales. | Es necesario verificar la cuenta, los créditos y los costos de los recursos. |
| Microsoft Azure | Cuenta con Azure for Students, que ofrece 100 USD de crédito durante 12 meses para estudiantes elegibles. | Los créditos y servicios disponibles dependen de los requisitos del programa. |
| AWS | Tiene varios servicios para desplegar aplicaciones y beneficios para cuentas nuevas. | Debemos revisar sus límites y costos para no consumir los créditos rápidamente. |

**Propuesta:** utilizar Google Cloud para comenzar las pruebas. Su crédito inicial puede ayudarnos a trabajar sin pagar directamente mientras esté disponible.

Si no podemos activar una cuenta o los recursos no son suficientes, consideraríamos Azure for Students como segunda opción.

## 3. Kubernetes

Kubernetes nos permitirá administrar los contenedores de los distintos servicios de Help Chair.

Se consideraron dos opciones:

- **GKE:** Kubernetes administrado por Google Cloud. Facilita algunas tareas de administración, pero puede generar costos adicionales.
- **k3s:** distribución ligera de Kubernetes que podemos instalar en una máquina virtual. Requiere que nosotros administremos el servidor.

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

Para tener una referencia, se tomó como ejemplo una máquina virtual e2-standard-2 de Google Cloud, con 2 vCPU y 8 GiB de memoria RAM, en la región us-central1.

El cálculo considera 730 horas de funcionamiento, aproximadamente un mes completo.

| Recurso | Costo mensual aproximado |
|---|---|
| Máquina virtual e2-standard-2 (730 horas) | 48.92 USD |
| Disco estándar de 30 GB | 1.20 USD |
| k3s | Sin costo de licencia |
| GHCR | Sin costo para imágenes públicas |
| NATS | Sin costo de licencia |
| **Subtotal estimado** | **50.12 USD** |

Este subtotal solo incluye el costo de una máquina virtual y su disco. No incluye tráfico de red, direcciones IP, otros servicios, impuestos ni posibles cargos adicionales.

Tanto k3s como NATS necesitan recursos del servidor para funcionar, aunque no tengan costo de licencia.

También hay que considerar que esta máquina es solamente una referencia para las pruebas iniciales. Todavía no sabemos si sus 8 GiB de RAM serán suficientes para ejecutar todos los servicios, sus bases de datos y las herramientas necesarias para Help Chair.

Por eso, los 50.12 USD no representan el costo mensual de todo el proyecto.

Google Cloud ofrece 300 USD de crédito durante 90 días para cuentas nuevas elegibles. Si logramos activar ese beneficio, podríamos utilizarlo para cubrir parte de los recursos durante las pruebas.

Antes de contratar o activar servicios debemos confirmar los créditos disponibles, los permisos de acceso y el consumo que tendrá el sistema.

Los precios también pueden cambiar dependiendo de la región y los recursos seleccionados.

## 7. Decisión propuesta

Para comenzar con el despliegue de Help Chair proponemos:

- **Nube:** Google Cloud.
- **Kubernetes:** k3s.
- **Registro de imágenes:** GHCR.
- **Broker:** NATS.

La propuesta busca que podamos comenzar las pruebas sin utilizar una infraestructura demasiado costosa.

Google Cloud nos parece una buena opción por los créditos iniciales, mientras que k3s permitiría trabajar con Kubernetes sin contratar directamente un clúster administrado.

GHCR y NATS también son opciones que podemos utilizar junto con las tecnologías que ya tiene contempladas el proyecto.

Todavía necesitamos confirmar que podamos acceder a Google Cloud, revisar el consumo real de los servicios y comprobar que las herramientas funcionen correctamente.

Esta decisión queda pendiente de aprobación por el equipo de Plataforma.

## 8. Fuentes consultadas

- Google Cloud: https://cloud.google.com/free
- Precios de Compute Engine: https://cloud.google.com/products/compute/pricing/general-purpose
- Precios de almacenamiento: https://cloud.google.com/products/block-storage
- Azure for Students: https://azure.microsoft.com/free/students/
- AWS: https://aws.amazon.com/free/
- k3s: https://docs.k3s.io/
- GitHub Container Registry: https://docs.github.com/en/packages
- NATS: https://docs.nats.io/
- RabbitMQ: https://www.rabbitmq.com/docs
