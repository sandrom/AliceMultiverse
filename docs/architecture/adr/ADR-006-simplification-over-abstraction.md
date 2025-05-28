# ADR-006: Simplification Over Abstraction

## Status
Proposed

## Context
A deep review of the AliceMultiverse codebase revealed significant over-engineering:

1. **Event System**: 5 different event store implementations (2,600+ lines) when only SQLite is used by default
2. **Provider System**: 4 layers of abstraction (2 base classes, 2 registries, event mixin, cost wrapper)
3. **Complexity Cost**: New contributors struggle with which base class/registry to use
4. **Performance Cost**: Every provider call goes through 4 layers of indirection
5. **Maintenance Cost**: Bug fixes and features require updating 4+ files

This violates our core principle from instructions.md: "be pragmatic, direct, no bullshit"

## Decision
We will simplify the architecture by:

1. **Event System**: Use PostgreSQL NOTIFY/LISTEN directly (400 lines vs 2,600)
2. **Provider System**: One base class, one registry (600 lines vs 1,500)
3. **Remove Abstraction Layers**: Delete compatibility wrappers and unused implementations

## Consequences

### Positive
- **85% code reduction** in event system (2,200 lines removed)
- **60% code reduction** in provider system (900 lines removed)
- **Easier onboarding**: Clear, direct architecture
- **Better performance**: Fewer method call layers
- **Lower maintenance**: Less code = fewer bugs
- **PostgreSQL-native**: Leverage database capabilities instead of emulating them

### Negative
- **Breaking changes**: Existing code must be migrated
- **Less flexibility**: Can't easily swap event stores (but we don't need to)
- **PostgreSQL dependency**: Can't use SQLite for development (acceptable trade-off)

### Neutral
- **Documentation updates**: All docs need revision
- **Test updates**: Tests must be rewritten for new interfaces

## Implementation Plan
14 commits as detailed in docs/architecture/simplification-plan.md:
- 3 commits for event system
- 4 commits for provider system
- 7 commits for critical issues and improvements

## Alternatives Considered

1. **Keep current abstractions**: Rejected - violates our principles and adds no value
2. **Partial simplification**: Rejected - half-measures won't solve the core issues
3. **Add more abstractions**: Rejected - would make the problem worse

## References
- instructions.md: Core development principles
- docs/architecture/simplification-plan.md: Detailed implementation plan
- Original event persistence: 320 lines provided same functionality