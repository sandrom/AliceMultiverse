{{/*
Expand the name of the chart.
*/}}
{{- define "alice-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "alice-service.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "alice-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "alice-service.labels" -}}
helm.sh/chart: {{ include "alice-service.chart" . }}
{{ include "alice-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "alice-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "alice-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "alice-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "alice-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database name
*/}}
{{- define "alice-service.databaseName" -}}
{{- default (include "alice-service.name" .) .Values.database.name }}
{{- end }}

{{/*
Database secret name
*/}}
{{- define "alice-service.databaseSecretName" -}}
{{ include "alice-service.fullname" . }}-db-credentials
{{- end }}

{{/*
Database cluster name
*/}}
{{- define "alice-service.databaseClusterName" -}}
{{ include "alice-service.fullname" . }}-db
{{- end }}

{{/*
Database connection string
*/}}
{{- define "alice-service.databaseUrl" -}}
{{- $dbName := include "alice-service.databaseName" . -}}
{{- $clusterName := include "alice-service.databaseClusterName" . -}}
{{- printf "postgresql://%s:$(DATABASE_PASSWORD)@%s-rw:5432/%s" .Values.database.user $clusterName $dbName -}}
{{- end }}