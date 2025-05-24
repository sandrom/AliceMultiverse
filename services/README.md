# AliceMultiverse Services

This directory contains all microservices that make up the AliceMultiverse system.

## Services

### Core Services
- **alice-interface**: Main orchestration and AI interface service
- **asset-processor**: Media processing and organization service
- **quality-analyzer**: Quality assessment pipeline service
- **metadata-extractor**: Metadata extraction and search service

### Future Services
- **workflow-engine**: Workflow orchestration service
- **storage-manager**: File storage and CDN integration
- **notification-service**: Event notifications and webhooks

## Architecture

All services follow these patterns:
- Event-driven communication via Redis Streams (or Dapr)
- Shared packages from `../packages`
- Independent deployment and scaling
- Health checks and metrics endpoints

## Service Structure

Each service contains:
```
service-name/
├── .claude-context.md    # AI assistant context
├── Dockerfile           # Container definition
├── pyproject.toml       # Dependencies
├── README.md           # Service documentation
├── src/
│   └── service_name/   # Source code
├── tests/              # Service tests
└── scripts/            # Utility scripts
```

## Running Services

### Development
```bash
cd services/asset-processor
pip install -e .
python -m asset_processor
```

### Docker
```bash
docker-compose up asset-processor
```

### Kubernetes
```bash
kubectl apply -f k8s/asset-processor.yaml
```