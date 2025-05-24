# Monorepo Structure

AliceMultiverse follows a monorepo architecture to manage shared code and services efficiently.

## Directory Structure

```
alicemultiverse/
├── packages/              # Shared packages
│   ├── alice-events/     # Event system and definitions
│   ├── alice-models/     # Data models and types
│   ├── alice-config/     # Configuration management
│   └── alice-utils/      # Common utilities
├── services/             # Microservices
│   ├── alice-interface/  # Main orchestration service
│   ├── asset-processor/  # Media processing service
│   ├── quality-analyzer/ # Quality assessment service
│   └── metadata-extractor/ # Metadata extraction service
├── alicemultiverse/      # Legacy monolithic code (being migrated)
├── tests/                # Integration tests
├── scripts/              # Build and maintenance scripts
├── docs/                 # Documentation
└── docker-compose.yml    # Local development environment
```

## Shared Packages

### alice-events
- Event definitions (Asset, Workflow, Creative events)
- Event bus implementation
- Redis Streams persistence
- Event monitoring utilities

### alice-models
- Core data models (Asset, Project, Workflow)
- Enumerations (MediaType, QualityRating, etc.)
- Type definitions
- Database models

### alice-config
- Configuration schema
- Environment variable handling
- Service-specific configurations
- Feature flags

### alice-utils
- File operations
- Media detection and processing
- Hashing utilities
- Common helpers

## Services

Each service:
- Has its own `pyproject.toml` with dependencies
- Includes a `.claude-context.md` for AI assistance
- Provides Docker support
- Exposes REST API and/or event handlers
- Can be deployed independently

### alice-interface
The main orchestration service that:
- Handles AI assistant requests
- Orchestrates workflows across services
- Manages project context
- Provides unified API

### asset-processor
Handles media processing:
- File discovery and organization
- Format conversion
- Metadata extraction
- Event publishing

### quality-analyzer
Performs quality assessment:
- BRISQUE analysis
- External API integration (SightEngine, Claude)
- Quality scoring and rating
- Defect detection

### metadata-extractor
Extracts and indexes metadata:
- EXIF data extraction
- AI parameter extraction
- Metadata search
- Embedding generation

## Development Workflow

### Setup
```bash
# Install all packages in development mode
make install-dev

# Run tests
make test

# Start services locally
docker-compose up
```

### Adding a New Service
1. Create service directory: `services/my-service/`
2. Add `pyproject.toml` with dependencies
3. Create source in `src/my_service/`
4. Add Dockerfile
5. Update `docker-compose.yml`
6. Add to monorepo.toml

### Working on a Package
```bash
cd packages/alice-events
pip install -e .
# Make changes
pytest tests/
```

### Building for Production
```bash
# Build all packages
make build

# Build Docker images
make docker-build

# Push to registry
make docker-push
```

## Benefits

1. **Code Sharing**: Common code in packages, no duplication
2. **Independent Deployment**: Services can be deployed separately
3. **Consistent Tooling**: Same build/test/deploy process
4. **Atomic Changes**: Related changes across services in one commit
5. **Simplified Dependencies**: Internal packages always in sync

## Migration Strategy

The legacy code in `alicemultiverse/` is being gradually migrated:
1. Extract shared code to packages
2. Create service-specific implementations
3. Maintain backward compatibility during transition
4. Remove legacy code once migration complete