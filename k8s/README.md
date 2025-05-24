# AliceMultiverse Kubernetes Deployment

This directory contains everything needed to deploy AliceMultiverse on a local Kubernetes cluster (Docker Desktop on Mac).

## Quick Start

```bash
# Complete setup from scratch
./setup-all.sh

# Test the deployment
kubectl port-forward -n alice-assets svc/asset-processor-alice-service 8001:80
curl http://localhost:8001/health
```

## What Gets Deployed

1. **CloudNativePG Operator** - PostgreSQL management
2. **Redis** (single instance) - Event bus
3. **Asset Processor Service** - Media file processing with its own PostgreSQL database

All components are optimized for single-machine development:
- Single Redis instance (no replicas)
- Single PostgreSQL instance per service
- Minimal resource requirements

## Directory Structure

```
k8s/
├── README.md                 # This file
├── setup-all.sh             # One-command setup script
└── bootstrap/
    ├── bootstrap.sh         # Install prerequisites
    ├── deploy-redis.sh      # Deploy Redis
    ├── reset-cluster.sh     # Clean everything
    ├── pooler-crd.yaml      # CloudNativePG fix
    └── redis-single.yaml    # Redis configuration
```

## Detailed Setup Steps

### 1. Prerequisites

Ensure you have:
- Docker Desktop with Kubernetes enabled
- `kubectl` command-line tool
- `helm` package manager

The bootstrap script will verify these for you.

### 2. Run Complete Setup

```bash
cd k8s
./setup-all.sh
```

This script will:
1. Install CloudNativePG operator
2. Create all namespaces
3. Deploy Redis (single instance)
4. Build Docker images
5. Deploy services with Helm

### 3. Verify Deployment

```bash
# Check all pods
kubectl get pods --all-namespaces | grep alice-

# Check specific service
kubectl get all -n alice-assets

# View logs
kubectl logs -n alice-assets -l app.kubernetes.io/name=asset-processor -f
```

## Manual Steps

If you prefer to run steps individually:

```bash
# 1. Bootstrap prerequisites
./bootstrap/bootstrap.sh

# 2. Deploy Redis
./bootstrap/deploy-redis.sh

# 3. Build services (from root directory)
cd ..
docker build -t alice-assets:latest services/asset-processor

# 4. Deploy services
helm install asset-processor charts/alice-service \
  -f services/asset-processor/k8s-values.yaml \
  -n alice-assets
```

## Reset Everything

To completely remove all AliceMultiverse resources:

```bash
./bootstrap/reset-cluster.sh
```

**WARNING**: This will delete:
- All namespaces and their contents
- All databases and persistent data
- CloudNativePG operator
- Redis instance

## Service Access

### Port Forwarding

```bash
# Asset Processor
kubectl port-forward -n alice-assets svc/asset-processor-alice-service 8001:80

# Redis
kubectl port-forward -n alice-events svc/alice-events-redis-master 6379:6379

# PostgreSQL (Asset Processor DB)
kubectl port-forward -n alice-assets svc/asset-processor-alice-service-db-rw 5432:5432
```

### Service URLs (Internal)

- Asset Processor: `http://asset-processor-alice-service.alice-assets.svc.cluster.local`
- Redis: `redis://alice-events-redis-master.alice-events.svc.cluster.local:6379`
- PostgreSQL: `postgresql://alice:password@asset-processor-alice-service-db-rw.alice-assets.svc.cluster.local:5432/assets`

## Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Image Pull Errors

For Docker Desktop, ensure images are built locally:
```bash
docker images | grep alice-
```

### Database Connection Issues

```bash
# Check database pod
kubectl get pods -n alice-assets -l cnpg.io/cluster

# Check database logs
kubectl logs -n alice-assets -l cnpg.io/cluster
```

### Reset Stuck Namespace

If a namespace gets stuck during deletion:
```bash
kubectl get namespace <namespace> -o json | \
  jq '.spec.finalizers = []' | \
  kubectl replace --raw "/api/v1/namespaces/<namespace>/finalize" -f -
```

## Adding New Services

1. Create a Dockerfile in `services/<service-name>/`
2. Create `k8s-values.yaml` with service configuration
3. Build image: `docker build -t alice-<service>:latest services/<service-name>`
4. Deploy: `helm install <service> charts/alice-service -f services/<service>/k8s-values.yaml -n alice-<namespace>`

## Resource Requirements

Minimal requirements for local development:
- 4GB RAM allocated to Docker Desktop
- 2 CPU cores
- 10GB disk space

Current resource usage (approximate):
- CloudNativePG operator: 100Mi RAM, 100m CPU
- Redis: 128Mi RAM, 100m CPU
- Asset Processor: 256Mi RAM, 200m CPU
- PostgreSQL (per service): 256Mi RAM, 100m CPU

## Next Steps

After setup:
1. Access the Asset Processor API docs: http://localhost:8001/docs
2. Monitor events: `kubectl logs -n alice-assets -l app.kubernetes.io/name=asset-processor -f`
3. Deploy additional services as needed

For production deployment, consider:
- Enabling authentication on Redis
- Configuring PostgreSQL backups
- Setting up monitoring (Prometheus/Grafana)
- Implementing proper secrets management
- Adding resource limits and autoscaling