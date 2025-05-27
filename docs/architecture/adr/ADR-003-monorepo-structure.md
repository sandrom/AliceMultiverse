# ADR-003: Monorepo for Service Evolution

**Status**: Accepted  
**Date**: 2024-01-20  
**Context**: Repository Structure

## Context

AliceMultiverse is evolving from a monolithic application to a distributed system. We need a repository structure that:
- Supports gradual service extraction
- Maintains code sharing efficiency
- Enables independent service deployment
- Preserves development velocity
- Facilitates refactoring during transition

## Decision

Use a monorepo structure with clear package and service boundaries:

```
alicemultiverse/
├── packages/              # Shared packages
│   ├── alice-events/     # Event definitions and bus
│   ├── alice-models/     # Shared data models
│   ├── alice-config/     # Configuration management
│   └── alice-utils/      # Common utilities
├── services/             # Extracted microservices
│   ├── alice-interface/  # Main orchestration service
│   ├── asset-processor/  # Media processing service
│   └── [future services]
├── alicemultiverse/      # Legacy monolith (shrinking)
└── tests/                # Integration tests
```

## Rationale

### Why Monorepo?

1. **Atomic Changes**: Refactoring across service boundaries in one commit
2. **Code Sharing**: Shared packages without versioning overhead
3. **Consistent Tooling**: Single build system and standards
4. **Easier Refactoring**: Move code between services easily
5. **Unified Testing**: Integration tests across all services

### Why Not Polyrepo?

**Separate Repositories**:
- Versioning overhead for shared code
- Difficult cross-service refactoring
- Complex dependency management
- Slower development during transition

**Premature Service Boundaries**:
- Don't know final service shapes yet
- Need flexibility to move code
- Want to discover boundaries organically

### Package Strategy

**Shared Packages** (`packages/`):
- Event definitions (source of truth)
- Data models (ensure consistency)
- Configuration schemas
- Common utilities

**Services** (`services/`):
- Business logic
- API endpoints
- Service-specific code
- Independent deployment

**Legacy Code** (`alicemultiverse/`):
- Gradually shrinking
- Extract piece by piece
- Delete when empty

## Consequences

### Positive
- Fast refactoring during transition
- No version conflicts in shared code
- Easy to test integration scenarios
- Single source of truth for events/models
- Simplified local development

### Negative
- Larger repository size
- Need good CI/CD boundaries
- Risk of tight coupling
- Must enforce service boundaries
- Complex build configuration

### Migration Strategy

1. **Phase 1**: Create shared packages
   - Extract events, models, utils
   - Keep backward compatibility

2. **Phase 2**: Extract services gradually
   - Start with clear boundaries (asset processing)
   - Move code with its tests
   - Maintain monolith functionality

3. **Phase 3**: Shrink monolith
   - Delete extracted code
   - Update imports to packages
   - Eventually remove legacy code

### Enforcement Rules

1. Services cannot import from each other
2. Services only import from packages/
3. Packages cannot import from services
4. Legacy code can import from packages
5. New features go directly to services

## Implementation Guidelines

```python
# Good: Service imports from packages
from alice_events import AssetProcessedEvent
from alice_models import Asset
from alice_utils import calculate_hash

# Bad: Service imports from another service
# from services.asset_processor import process  # ❌

# Bad: Service imports from legacy
# from alicemultiverse.organizer import organize  # ❌
```

### Build System

- Separate package.json/pyproject.toml per package/service
- Workspace configuration for dependency management
- Independent versioning when ready to split
- Shared development dependencies

## References

- Monorepo Structure documentation
- Google's Monorepo approach
- Babel/React monorepo patterns
- Microservices extraction patterns