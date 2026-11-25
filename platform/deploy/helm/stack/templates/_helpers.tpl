{{/*
Todos los servicios, con sus valores ya combinados. Devuelve YAML: se usa como
  {{ $services := include "stack.services" . | fromYaml }}
Prioridad: defaults  <  services/<nombre>.yaml  <  serviceOverrides.<nombre>
*/}}
{{- define "stack.services" -}}
{{- $root := . -}}
{{- $out := dict -}}
{{- range $path, $_ := .Files.Glob "services/*.yaml" -}}
{{- $svc := $root.Files.Get $path | fromYaml -}}
{{- $expected := base $path | trimSuffix ".yaml" -}}
{{- if ne (toString $svc.name) $expected -}}
{{- fail (printf "%s: 'name' debe ser %q (el mismo que el nombre del archivo)" $path $expected) -}}
{{- end -}}
{{- if not $svc.port -}}
{{- fail (printf "%s: falta 'port'" $path) -}}
{{- end -}}
{{- $over := get (default dict $root.Values.serviceOverrides) $expected | default dict -}}
{{- $merged := mustMergeOverwrite (deepCopy $root.Values.defaults) $svc $over -}}
{{- $_ := set $out $expected $merged -}}
{{- end -}}
{{- toYaml $out -}}
{{- end -}}

{{/* Etiquetas comunes. Parámetros: root, name, component */}}
{{- define "stack.labels" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .root.Values.global.tenantId | quote }}
app.kubernetes.io/component: {{ .component }}
app.kubernetes.io/part-of: help-chair
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .root.Chart.Name .root.Chart.Version | quote }}
{{- end -}}

{{/* Etiquetas del selector (inmutables). Parámetros: root, name */}}
{{- define "stack.selector" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .root.Values.global.tenantId | quote }}
{{- end -}}

{{/* Imagen del servicio: <registro>/<repositorio>:<etiqueta> */}}
{{- define "stack.image" -}}
{{- $tag := default (required "global.imageTag es obligatorio (usa --set global.imageTag=<sha-del-commit>)" .root.Values.global.imageTag) .svc.image.tag -}}
{{- printf "%s/%s:%s" .root.Values.global.imageRegistry (required (printf "%s: falta image.repository" .name) .svc.image.repository) $tag -}}
{{- end -}}

{{- define "stack.secretName" -}}
{{- default (printf "%s-secret" .name) .svc.secretName -}}
{{- end -}}

{{- define "stack.dbUser" -}}{{- default .name .svc.db.user -}}{{- end -}}
{{- define "stack.dbName" -}}{{- default .name .svc.db.name -}}{{- end -}}

{{/* Variables no secretas del servicio (ConfigMap). Todo se convierte en texto. */}}
{{- define "stack.appConfig" -}}
{{- $root := .root -}}
{{- $svc := .svc -}}
{{- $cfg := dict "SERVICE_NAME" .name "PORT" (toString (int $svc.port)) "DEBUG" (toString $svc.debug) "LOG_LEVEL" $svc.logLevel "ALLOWED_HOSTS" $svc.allowedHosts "WEB_CONCURRENCY" (toString (int $svc.workers)) "TENANT_ID" $root.Values.global.tenantId "EMPRESA_ID" $root.Values.global.tenantId -}}
{{- if $root.Values.broker.enabled -}}
{{- $_ := set $cfg "BROKER_URL" "nats://broker:4222" -}}
{{- end -}}
{{- if $root.Values.mailpit.enabled -}}
{{- $_ := set $cfg "EMAIL_HOST" "mailpit" -}}
{{- $_ := set $cfg "EMAIL_PORT" "1025" -}}
{{- else if $root.Values.smtp.host -}}
{{- $_ := set $cfg "EMAIL_HOST" $root.Values.smtp.host -}}
{{- $_ := set $cfg "EMAIL_PORT" (toString (int $root.Values.smtp.port)) -}}
{{- end -}}
{{- range $k, $v := (default dict $svc.env) -}}
{{- $_ := set $cfg $k (toString $v) -}}
{{- end -}}
{{- toYaml $cfg -}}
{{- end -}}

{{/* Variables secretas y DATABASE_URL (sirve para el contenedor y para el initContainer) */}}
{{- define "stack.appEnv" -}}
{{- $secret := include "stack.secretName" . -}}
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ $secret }}
      key: SECRET_KEY
{{- if .svc.db.enabled }}
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ $secret }}
      key: POSTGRES_PASSWORD
- name: DATABASE_URL
  value: {{ printf "postgresql://%s:$(POSTGRES_PASSWORD)@%s-db:5432/%s" (include "stack.dbUser" .) .name (include "stack.dbName" .) | quote }}
{{- end }}
{{- end -}}
