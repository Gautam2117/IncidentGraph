{{/*
Expand the name of the chart.
*/}}
{{- define "incidentgraph.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "incidentgraph.labels" -}}
app.kubernetes.io/name: {{ include "incidentgraph.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "incidentgraph.serviceAccountName" -}}
{{- default (include "incidentgraph.fullname" .) .Values.serviceAccount.name }}
{{- end }}

{{- define "incidentgraph.controlPlaneEnv" -}}
- name: APP_ENV
  value: production
- name: ENVIRONMENT
  value: production
- name: DEBUG
  value: "false"
- name: DATABASE_URL
  valueFrom:
    secretKeyRef: { name: {{ .Values.existingSecret }}, key: database-url }
- name: SECRET_KEY
  valueFrom:
    secretKeyRef: { name: {{ .Values.existingSecret }}, key: secret-key }
- name: WEBHOOK_SIGNING_SECRET
  valueFrom:
    secretKeyRef: { name: {{ .Values.existingSecret }}, key: webhook-signing-secret }
- name: REDIS_URL
  value: redis://{{ include "incidentgraph.fullname" . }}-redis:6379/0
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: http://{{ include "incidentgraph.fullname" . }}-otel-collector:4317
- name: PROMETHEUS_URL
  value: http://{{ include "incidentgraph.fullname" . }}-prometheus:9090
- name: LOKI_URL
  value: http://{{ include "incidentgraph.fullname" . }}-loki:3100
- name: TEMPO_URL
  value: http://{{ include "incidentgraph.fullname" . }}-tempo:3200
- name: DEMO_GATEWAY_URL
  value: http://gateway:8000
- name: DEMO_AUTH_URL
  value: http://auth:8000
- name: DEMO_ORDERS_URL
  value: http://orders:8000
- name: DEMO_PAYMENTS_URL
  value: http://payments:8000
- name: DEMO_INVENTORY_URL
  value: http://inventory:8000
- name: DEMO_NOTIFICATIONS_URL
  value: http://notifications:8000
- name: EMBEDDING_PROVIDER
  value: local
- name: EMBEDDING_MODEL
  value: BAAI/bge-small-en-v1.5
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "incidentgraph.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}
