# ADR-001: Event-Driven Architecture

**Status**: Accepted  
**Date**: 2024-01-15  
**Context**: System Architecture Foundation

## Context

AliceMultiverse started as a monolithic media organizer but is evolving into a comprehensive creative workflow hub. We need an architecture that:
- Supports gradual extraction of services
- Enables loose coupling between components
- Captures the non-linear nature of creative work
- Provides observability into system operations
- Scales from single-user to enterprise deployments

## Decision

Implement an event-driven architecture as the foundation for all component communication. All significant operations will publish events that other components can subscribe to.

### Event Categories
1. **Asset Events**: File discovery, processing, organization
2. **Workflow Events**: Pipeline execution, stage transitions
3. **Creative Events**: Project creation, style changes, context updates

### Implementation Approach
- Start with in-process event bus for simplicity
- Add optional Redis persistence for durability
- Plan for Dapr/Kafka when scale demands

## Rationale

### Why Event-Driven?

1. **Loose Coupling**: Components don't need to know about each other
2. **Evolution Path**: Easy to extract services without changing logic
3. **Creative Workflows**: Events naturally model non-linear creative processes
4. **Observability**: Every action generates trackable events
5. **Flexibility**: New features can subscribe to existing events

### Why Not Direct Calls?

Direct method calls create tight coupling that makes it difficult to:
- Extract services later
- Add new features without modifying existing code
- Track what's happening in the system
- Support distributed deployments

### Progressive Enhancement

Starting simple (in-process) but designing for distribution:
```
Phase 1: In-process EventBus (current)
Phase 2: Redis Streams persistence (optional)
Phase 3: Dapr for service mesh (future)
Phase 4: Kafka for high scale (eventual)
```

## Consequences

### Positive
- Clean service boundaries from the start
- Easy to add monitoring and analytics
- Natural audit trail of all operations
- Supports both sync and async patterns
- Enables event sourcing if needed

### Negative
- Slight complexity increase for simple operations
- Need to define event schemas
- Potential for event storms if not careful
- Debugging across event boundaries harder

### Implementation Example

```python
# Publishing events
await event_bus.publish(AssetDiscoveredEvent(
    asset_id=asset.id,
    path=str(file_path),
    metadata=metadata
))

# Subscribing to events
@event_bus.subscribe(AssetDiscoveredEvent)
async def handle_asset_discovered(event: AssetDiscoveredEvent):
    # Process the discovered asset
    pass
```

## References

- Event-Driven Architecture documentation
- Domain-Driven Design by Eric Evans
- Enterprise Integration Patterns
- CQRS and Event Sourcing patterns