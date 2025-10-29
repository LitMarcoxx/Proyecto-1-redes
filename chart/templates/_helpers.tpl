{{- define "dns-project.name" -}}
dns-api
{{- end -}}

{{- define "dns-project.fullname" -}}
{{ include "dns-project.name" . }}-{{ .Release.Name }}
{{- end -}}
