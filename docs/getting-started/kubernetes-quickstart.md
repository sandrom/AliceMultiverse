# Kubernetes Quick Start Guide

This guide gets you running AliceMultiverse on local Kubernetes in under 10 minutes.

## Prerequisites

Ensure you have:
- Docker Desktop with Kubernetes enabled
- `kubectl` command working
- Active `docker-desktop` context

Verify with:
```bash
kubectl config current-context
# Should output: docker-desktop

kubectl get nodes
# Should show one node in Ready state
```

## Step 1: Install CloudNativePG

```bash
# Install the PostgreSQL operator
kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.23/releases/cnpg-1.23.0.yaml

# Wait for operator to be ready (takes ~30 seconds)
kubectl wait --for=condition=Available deployment/cnpg-controller-manager -n cnpg-system --timeout=120s
```

## Step 2: Create Namespaces

```bash
# Create all service namespaces at once
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: alice-interface
---
apiVersion: v1
kind: Namespace
metadata:
  name: alice-assets
---
apiVersion: v1
kind: Namespace
metadata:
  name: alice-events
EOF
```

## Step 3: Deploy Redis Event Bus

```bash
# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install Redis
helm install alice-events bitnami/redis \
  --namespace alice-events \
  --set auth.enabled=false \
  --set master.persistence.size=1Gi
```

## Step 4: Deploy First Service (Asset Processor)

Create deployment configuration:

```bash
# Create temporary deployment file
cat <<'EOF' > /tmp/asset-processor-k8s.yaml
# Database
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: asset-db
  namespace: alice-assets
spec:
  instances: 1
  postgresql:
    parameters:
      max_connections: "50"
  bootstrap:
    initdb:
      database: assets
      owner: alice
      secret:
        name: asset-db-credentials
  storage:
    size: 1Gi
---
# Database Secret
apiVersion: v1
kind: Secret
metadata:
  name: asset-db-credentials
  namespace: alice-assets
type: Opaque
stringData:
  username: alice
  password: localdev123
  uri: postgresql://alice:localdev123@asset-db-rw:5432/assets
---
# Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asset-processor
  namespace: alice-assets
spec:
  replicas: 1
  selector:
    matchLabels:
      app: asset-processor
  template:
    metadata:
      labels:
        app: asset-processor
    spec:
      containers:
      - name: asset-processor
        image: alice-assets:local
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: asset-db-credentials
              key: uri
        - name: REDIS_URL
          value: redis://alice-events-redis-master.alice-events.svc.cluster.local:6379
---
# Service
apiVersion: v1
kind: Service
metadata:
  name: asset-processor
  namespace: alice-assets
spec:
  selector:
    app: asset-processor
  ports:
  - port: 80
    targetPort: 8000
EOF

# Apply the configuration
kubectl apply -f /tmp/asset-processor-k8s.yaml
```

## Step 5: Build and Load Docker Image

```bash
# Build the asset processor image
cd services/asset-processor
docker build -t alice-assets:local .

# No need to push - docker-desktop shares images automatically
```

## Step 6: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n alice-assets

# Check database is ready
kubectl wait --for=condition=Ready pod -l cnpg.io/cluster=asset-db -n alice-assets --timeout=120s

# Port forward to test the service
kubectl port-forward -n alice-assets svc/asset-processor 8001:80 &

# Test the service
curl http://localhost:8001/health
```

## Step 7: Access Database

```bash
# Port forward to database
kubectl port-forward -n alice-assets svc/asset-db-rw 5432:5432 &

# Connect with psql (if installed)
PGPASSWORD=localdev123 psql -h localhost -U alice -d assets

# Or use kubectl exec
kubectl exec -it -n alice-assets asset-db-1 -- psql -U alice -d assets
```

## Useful Commands

### View logs
```bash
# Application logs
kubectl logs -n alice-assets -l app=asset-processor -f

# Database logs
kubectl logs -n alice-assets -l cnpg.io/cluster=asset-db -f
```

### Clean up
```bash
# Delete everything in a namespace
kubectl delete all --all -n alice-assets

# Delete the namespace
kubectl delete namespace alice-assets
```

### Troubleshooting
```bash
# Describe pod for errors
kubectl describe pod -n alice-assets

# Get events
kubectl get events -n alice-assets --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n alice-assets
```

## Next Steps

1. **Add Monitoring**: Install Kubernetes Dashboard or k9s for visual management
2. **Setup Skaffold**: For automatic rebuilds during development
3. **Create Helm Charts**: For easier deployment management
4. **Add More Services**: Follow the same pattern for other microservices

## Tips for Local Development

1. **Resource Limits**: Keep them low for local development
2. **Image Pull Policy**: Use `imagePullPolicy: Never` for local images
3. **Persistence**: Use small volume sizes (1-5Gi) locally
4. **Port Forwarding**: Use kubectl port-forward for quick access
5. **Namespace Isolation**: Each service in its own namespace for clarity

## Common Issues

### Pod stuck in Pending
```bash
# Check for resource constraints
kubectl describe pod <pod-name> -n <namespace>

# Usually means insufficient resources - reduce requests/limits
```

### Database connection refused
```bash
# Ensure database is ready
kubectl get pods -n alice-assets -l cnpg.io/cluster=asset-db

# Check secret is created
kubectl get secret asset-db-credentials -n alice-assets
```

### Image not found
```bash
# For local images, ensure imagePullPolicy: Never
# Rebuild and ensure docker-desktop context is active
docker build -t alice-assets:local .
```

This quickstart gets you running with one service. Repeat steps 4-6 for additional services, adjusting names and ports accordingly.