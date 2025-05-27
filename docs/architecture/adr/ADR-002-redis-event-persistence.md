# ADR-002: Redis Streams for Event Persistence

**Status**: Accepted  
**Date**: 2024-01-16  
**Context**: Event System Implementation

## Context

Following ADR-001's event-driven architecture decision, we need to choose how to persist events for:
- Durability across restarts
- Event replay capabilities
- Distributed processing support
- Development and debugging
- Future microservices communication

## Decision

Use Redis Streams as the primary event persistence mechanism, with it being an optional feature that can be enabled when needed.

### Key Design Choices
1. Redis Streams over Redis Pub/Sub for persistence
2. Optional dependency - system works without Redis
3. Consumer groups for distributed processing
4. Automatic stream trimming to control memory
5. Standard stream key format: `alice:events:{category}:{type}`

## Rationale

### Why Redis Streams?

1. **Built-in Persistence**: Unlike pub/sub, streams store messages
2. **Consumer Groups**: Native support for distributed processing
3. **Ordered Delivery**: Guaranteed message ordering
4. **Simple Operations**: Easy to implement and debug
5. **Good Performance**: Suitable for our throughput needs

### Why Not Alternatives?

**Kafka**: 
- Overkill for current scale
- Complex operational overhead
- Can migrate later if needed

**RabbitMQ/AMQP**:
- More complex than needed
- Less suitable for event sourcing
- Requires separate persistence

**PostgreSQL LISTEN/NOTIFY**:
- No built-in persistence
- Limited to single database
- Not designed for high throughput

**In-Memory Only**:
- Loses events on restart
- No replay capability
- Can't support distributed processing

### Optional Dependency

Making Redis optional provides:
- Zero infrastructure for development
- Easy local testing
- Gradual adoption path
- Reduced complexity for simple deployments

## Consequences

### Positive
- Simple local development (no Redis required)
- Built-in durability and replay
- Native consumer group support
- Good monitoring with Redis tools
- Easy to understand and debug

### Negative
- Another infrastructure component in production
- Redis memory usage grows with events
- Need to manage stream trimming
- Single point of failure (unless clustered)

### Implementation Details

```python
# Configuration
persistence = EventPersistence(
    redis_url="redis://localhost:6379",
    stream_prefix="alice:events:",
    consumer_group="alice-main",
    max_len=100000  # Trim streams to 100k events
)

# Publishing with persistence
await event_bus.publish(event)  # Automatically persisted if Redis connected

# Consumer groups for scaling
async for event in persistence.consume(
    categories=["asset", "workflow"],
    consumer_name="worker-1"
):
    await process_event(event)
```

### Migration Path

When scale demands:
1. Add Dapr with Redis state store
2. Gradually move to Dapr pubsub
3. Eventually replace with Kafka if needed
4. Keep same event schemas throughout

## References

- Redis Streams documentation
- Event Persistence implementation guide
- Consumer Groups pattern
- Event Sourcing with Redis Streams