
# Recursos y capacidad de Help Chair

## Objetivo

Definir los recursos iniciales para los servicios de Help Chair y establecer cómo vamos a medir el consumo de CPU y memoria en Kubernetes.

Este documento corresponde al Issue #94 de Plataforma de Deployment.

## Configuración inicial

Se agregó el archivo `platform/deploy/k8s/testing-resources.yaml` con un LimitRange y un ResourceQuota para el namespace `testing`.

Los valores son iniciales y deberán ajustarse después de realizar pruebas con los servicios funcionando.

| Recurso | Valor |
|---|---|
| CPU solicitada por contenedor | 100m |
| Memoria solicitada por contenedor | 128Mi |
| Límite de CPU por contenedor | 500m |
| Límite de memoria por contenedor | 512Mi |
| CPU solicitada total del namespace | 4 CPU |
| Memoria solicitada total | 8Gi |
| CPU máxima declarada del namespace | 8 CPU |
| Memoria máxima declarada del namespace | 12Gi |
| Máximo de pods | 30 |

## Medición de consumo

Para medir los recursos será necesario tener acceso al clúster y contar con Metrics Server funcionando.

Primero se revisarán los nodos y pods:

```bash
kubectl get nodes
kubectl get pods -n testing
```

Después se medirá el consumo:

```bash
kubectl top nodes
kubectl top pods -n testing --containers
```

También se comprobarán las cuotas:

```bash
kubectl describe resourcequota -n testing
kubectl describe limitrange -n testing
```

### Resultados de las mediciones

Pendiente de ejecutar en el clúster de pruebas.

Todavía no se cuenta con resultados reales de CPU y memoria para registrar en este documento.

Cuando se realicen las pruebas se anotarán la fecha, el nodo utilizado, los servicios desplegados, el consumo observado y los resultados de los comandos.

## Estimación de memoria por stack

Para una primera aproximación se considera que cada empresa tendrá seis servicios y seis bases de datos.

Se utiliza el valor inicial de 128Mi de memoria solicitada por contenedor como referencia, suponiendo un contenedor por servicio y otro por base de datos.

| Componente | Cantidad | Memoria solicitada |
|---|---:|---:|
| Servicios | 6 | 768Mi |
| Bases de datos | 6 | 768Mi |
| Total estimado | 12 | 1536Mi |

Esta cifra es un ejemplo de planificación, no una medición real. Las bases de datos podrían necesitar más memoria y los componentes compartidos, como gateway y monitoreo, no están incluidos.

## Estimación de stacks por nodo

Para calcular cuántos stacks caben se debe conocer la memoria asignable del nodo, reservar recursos para Kubernetes y considerar los componentes compartidos.

La fórmula inicial es:

`Stacks = memoria disponible para aplicaciones / memoria solicitada por stack`

El resultado debe redondearse hacia abajo.

Además de la memoria, se deben comprobar los recursos de CPU, las cuotas, el almacenamiento y la cantidad máxima de pods.

No se define todavía una cantidad real de stacks por nodo porque falta conocer la capacidad del clúster y medir el consumo de los servicios.

## Pendientes de validación

- Confirmar la capacidad real de los nodos.
- Validar el manifiesto de Kubernetes.
- Comprobar que existe el namespace `testing`.
- Aplicar LimitRange y ResourceQuota en un entorno autorizado.
- Ejecutar `kubectl top` con los servicios funcionando.
- Registrar las mediciones reales.
- Ajustar los valores y calcular la capacidad por nodo.
