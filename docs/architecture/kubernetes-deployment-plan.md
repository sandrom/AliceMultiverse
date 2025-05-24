# Kubernetes Deployment Plan

## Overview

This document outlines the migration strategy from local development to Kubernetes-based microservices deployment for AliceMultiverse. Each service will have its own isolated database, and we'll use Helm charts for deployment management.

## Architecture Principles

1. **Database Isolation**: Each service owns its database - no shared databases
2. **Network Segmentation**: Services can only access their own databases
3. **GitOps Ready**: Structure supports automated deployment pipelines
4. **Local-First**: Optimized for docker-desktop Kubernetes development
5. **Production-Scalable**: Can grow from local to cloud deployment

## Technology Stack

### Core Components
- **Kubernetes**: Docker Desktop's local Kubernetes
- **Database Operator**: CloudNativePG for PostgreSQL management
- **Package Manager**: Helm v3 for application deployment
- **Development Tool**: Skaffold for hot-reload development
- **Service Mesh**: Istio (optional, for advanced traffic management)

### Why CloudNativePG?
- Designed for microservices (one DB per service pattern)
- Simple configuration and operation
- Active open-source community
- Native Kubernetes integration
- No complex dependencies

## Implementation Steps

### Phase 1: Infrastructure Setup

#### 1.1 Install CloudNativePG Operator
```bash
# Install the operator
kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.23/releases/cnpg-1.23.0.yaml

# Verify installation
kubectl get deployment -n cnpg-system cnpg-controller-manager
```

#### 1.2 Create Service Namespaces
```bash
# Core services
kubectl create namespace alice-interface
kubectl create namespace alice-assets
kubectl create namespace alice-quality
kubectl create namespace alice-metadata
kubectl create namespace alice-search
kubectl create namespace alice-workflow

# Shared infrastructure
kubectl create namespace alice-events
kubectl create namespace alice-monitoring
```

#### 1.3 Setup Development Tools
```bash
# Install Skaffold
brew install skaffold

# Install Helm
brew install helm

# Install k9s for cluster management (optional but recommended)
brew install k9s
```

### Phase 2: Create Base Helm Chart

#### 2.1 Base Chart Structure
```
charts/
└── alice-service/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        ├── configmap.yaml
        ├── secret.yaml
        ├── database.yaml
        ├── networkpolicy.yaml
        └── _helpers.tpl
```

#### 2.2 Base Chart Configuration
```yaml
# charts/alice-service/values.yaml
replicaCount: 1

image:
  repository: ""
  pullPolicy: IfNotPresent
  tag: ""

service:
  type: ClusterIP
  port: 80

database:
  enabled: true
  size: 1Gi
  instances: 1

redis:
  enabled: true

env: []

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

#### 2.3 Database Template
```yaml
# charts/alice-service/templates/database.yaml
{{- if .Values.database.enabled }}
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: {{ include "alice-service.fullname" . }}-db
  namespace: {{ .Release.Namespace }}
spec:
  instances: {{ .Values.database.instances }}
  postgresql:
    parameters:
      max_connections: "100"
      shared_buffers: "256MB"
  bootstrap:
    initdb:
      database: {{ .Values.database.name | default .Chart.Name }}
      owner: {{ .Values.database.user | default "alice" }}
      secret:
        name: {{ include "alice-service.fullname" . }}-db-credentials
  storage:
    size: {{ .Values.database.size }}
    storageClass: standard
{{- end }}
```

### Phase 3: Dockerize Services

#### 3.1 Standard Dockerfile Template
```dockerfile
# Dockerfile.template
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . .

# Run as non-root
RUN useradd -m alice && chown -R alice:alice /app
USER alice

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.2 Build Configuration
```yaml
# skaffold.yaml
apiVersion: skaffold/v4beta6
kind: Config
metadata:
  name: alice-multiverse
build:
  artifacts:
  - image: alice-interface
    context: services/alice-interface
  - image: alice-assets
    context: services/asset-processor
  - image: alice-quality
    context: services/quality-analyzer
  - image: alice-metadata
    context: services/metadata-extractor
deploy:
  helm:
    releases:
    - name: alice-interface
      chartPath: charts/alice-service
      valuesFiles:
      - services/alice-interface/values.yaml
      namespace: alice-interface
    - name: alice-assets
      chartPath: charts/alice-service
      valuesFiles:
      - services/asset-processor/values.yaml
      namespace: alice-assets
```

### Phase 4: Service Configuration

#### 4.1 Asset Processor Example
```yaml
# services/asset-processor/values.yaml
image:
  repository: alice-assets
  tag: latest

service:
  port: 8001

database:
  enabled: true
  name: assets
  user: asset_service
  size: 5Gi

env:
  - name: SERVICE_NAME
    value: "asset-processor"
  - name: REDIS_URL
    value: "redis://alice-events-redis:6379"
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: alice-assets-db-credentials
        key: uri
```

#### 4.2 Network Policy
```yaml
# Ensure database isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-isolation
  namespace: {{ .Release.Namespace }}
spec:
  podSelector:
    matchLabels:
      cnpg.io/cluster: {{ include "alice-service.fullname" . }}-db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: {{ .Release.Namespace }}
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: {{ include "alice-service.name" . }}
    ports:
    - protocol: TCP
      port: 5432
```

### Phase 5: Event Bus Setup

#### 5.1 Shared Redis for Events
```yaml
# infrastructure/redis/values.yaml
architecture: standalone
auth:
  enabled: false  # For local dev
master:
  persistence:
    enabled: true
    size: 1Gi
```

```bash
# Deploy Redis
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install alice-events bitnami/redis \
  -f infrastructure/redis/values.yaml \
  -n alice-events
```

### Phase 6: Local Development Workflow

#### 6.1 Start Development
```bash
# Start all services with hot-reload
skaffold dev --port-forward

# Start specific service
skaffold dev --port-forward -m alice-assets

# Access services
# alice-interface: http://localhost:8000
# alice-assets: http://localhost:8001
# alice-quality: http://localhost:8002
```

#### 6.2 Database Access
```bash
# Get database credentials
kubectl get secret alice-assets-db-credentials \
  -n alice-assets \
  -o jsonpath='{.data.password}' | base64 -d

# Port forward to database
kubectl port-forward \
  -n alice-assets \
  svc/alice-assets-db-rw 5432:5432

# Connect with psql
psql -h localhost -U asset_service -d assets
```

### Phase 7: Monitoring and Observability

#### 7.1 Install Monitoring Stack
```bash
# Add Prometheus community charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Install kube-prometheus-stack
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n alice-monitoring \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=standard \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=5Gi
```

#### 7.2 Service Metrics
```python
# Add to each service
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Migration Checklist

### Prerequisites
- [ ] Docker Desktop with Kubernetes enabled
- [ ] kubectl configured for docker-desktop context
- [ ] Helm v3 installed
- [ ] Skaffold installed

### Infrastructure
- [ ] CloudNativePG operator deployed
- [ ] Service namespaces created
- [ ] Redis for event bus deployed
- [ ] Network policies configured

### Services
- [ ] Base Helm chart created
- [ ] Asset Processor dockerized and deployed
- [ ] Quality Analyzer dockerized and deployed
- [ ] Metadata Extractor dockerized and deployed
- [ ] Alice Interface dockerized and deployed

### Development Tools
- [ ] Skaffold configuration working
- [ ] Hot-reload verified
- [ ] Database connections tested
- [ ] Event bus communication verified

### Monitoring
- [ ] Prometheus deployed
- [ ] Grafana dashboards configured
- [ ] Service metrics exposed
- [ ] Alerts configured

## Best Practices

### 1. Database Management
- Use CloudNativePG's backup features
- Set appropriate resource limits
- Monitor connection pools
- Use read replicas for scaling

### 2. Secret Management
- Never commit secrets to Git
- Use Kubernetes secrets for sensitive data
- Consider Sealed Secrets for GitOps
- Rotate credentials regularly

### 3. Resource Management
- Set appropriate requests and limits
- Use HPA for autoscaling
- Monitor resource usage
- Plan for growth

### 4. Development Workflow
- Use Skaffold for rapid iteration
- Keep images small
- Use multi-stage builds
- Cache dependencies

## Troubleshooting

### Common Issues

#### Database Connection Failures
```bash
# Check database pod status
kubectl get pods -n alice-assets -l cnpg.io/cluster=alice-assets-db

# Check database logs
kubectl logs -n alice-assets alice-assets-db-1

# Verify secret exists
kubectl get secret -n alice-assets alice-assets-db-credentials
```

#### Service Discovery Issues
```bash
# Check service endpoints
kubectl get endpoints -n alice-assets

# Test DNS resolution
kubectl run -it --rm debug --image=alpine --restart=Never -- nslookup alice-assets-db-rw.alice-assets.svc.cluster.local
```

#### Event Bus Connection Issues
```bash
# Check Redis status
kubectl get pods -n alice-events

# Test Redis connection
kubectl run -it --rm redis-cli --image=redis --restart=Never -- redis-cli -h alice-events-redis.alice-events.svc.cluster.local ping
```

## Next Steps

1. **Implement CI/CD Pipeline**: Set up GitHub Actions for automated builds
2. **Add Service Mesh**: Consider Istio for advanced traffic management
3. **Implement GitOps**: Use ArgoCD for declarative deployments
4. **Add Backup Strategy**: Configure automated database backups
5. **Security Hardening**: Implement pod security policies and RBAC

## References

- [CloudNativePG Documentation](https://cloudnative-pg.io/documentation/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Skaffold Documentation](https://skaffold.dev/docs/)