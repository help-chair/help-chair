
# Política de imágenes GHCR - Help Chair

## Objetivo

Definir cómo se identificarán y almacenarán las imágenes de los servicios de Help Chair en GitHub Container Registry (GHCR).

## Registro de imágenes

Se utilizará GHCR con el siguiente formato:

`ghcr.io/help-chair/hc-<service>`

Cada imagen deberá estar vinculada al repositorio help-chair/help-chair.

La visibilidad de los paquetes deberá definirse antes de publicarlos. Si son privados, Jenkins y Kubernetes necesitarán permisos para acceder a ellos.

## Etiquetas

Para identificar las imágenes se utilizarán dos tipos de etiquetas:

- SHA del commit para cada construcción.
- Versión SemVer, por ejemplo `v1.0.0`, cuando se publique una versión.

No se utilizará la etiqueta `latest`.

## Publicación desde Jenkins

Jenkins utilizará la credencial `ghcr-push`, configurada mediante las variables `GHCR_USER` y `GHCR_TOKEN`.

El token deberá tener permisos para publicar paquetes en GHCR y nunca se guardará directamente en el repositorio.

La implementación del paso de publicación se coordinará con el responsable del Issue #88.

## Descarga desde Kubernetes

El clúster utilizará la imagen publicada en GHCR con una etiqueta específica.

Si las imágenes son privadas, se deberá configurar un `imagePullSecret` en el namespace correspondiente y asociarlo a los workloads que necesiten descargar las imágenes.

Las credenciales no deberán incluirse en los archivos versionados del proyecto.

## Pendientes de validación

- Comprobar que las imágenes estén vinculadas al repositorio.
- Verificar la visibilidad y permisos de los paquetes.
- Confirmar una publicación real desde Jenkins.
- Comprobar la descarga desde Kubernetes.
