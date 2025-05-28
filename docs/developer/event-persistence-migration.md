# Event System Persistence Migration Guide

This guide explains how to migrate from the basic event system to the enhanced persistent event system.

## Overview

The enhanced event system adds:
- **Flexible persistence backends** (Redis, SQLite, Memory)
- **Event schema versioning** with automatic migration
- **At-least-once delivery** guarantees
- **Dead letter queue** for failed events
- **Event replay** capabilities
- **Consumer groups** for distributed processing

## Quick Start

### 1. Basic Usage (SQLite Backend)

```python
from alicemultiverse.events.enhanced_bus import EnhancedEventBus
from alicemultiverse.events.base import create_event
from alicemultiverse.events.asset_events import AssetDiscoveredEvent

# Create enhanced bus (uses SQLite by default)
bus = EnhancedEventBus()
await bus.initialize()

# Publish events as before
event = create_event(
    AssetDiscoveredEvent,
    source="scanner",
    asset_id="abc123",
    file_path="/path/to/image.jpg",
    media_type="image",
    file_size=1024000,
    metadata={"width": 1920, "height": 1080}
)
await bus.publish(event)
```

### 2. Configuration

Set backend via environment variables:

```bash
# SQLite (default)
export EVENT_STORE_BACKEND=sqlite
export EVENT_STORE_PATH=~/.alicemultiverse/events.db

# Redis
export EVENT_STORE_BACKEND=redis
export REDIS_URL=redis://localhost:6379

# Memory (for testing)
export EVENT_STORE_BACKEND=memory
```

Or programmatically:

```python
from alicemultiverse.events.store import EventStoreConfig

config = EventStoreConfig(
    backend="redis",
    redis_url="redis://localhost:6379",
    max_events=100000,
    trim_interval_hours=24
)

bus = EnhancedEventBus()
await bus.initialize(config)
```

### 3. Persistent Subscriptions

Replace basic subscriptions with persistent ones:

```python
# Old way
subscriber = MyEventHandler(["asset.discovered"])
bus.subscribe(subscriber)

# New way - with delivery guarantees
subscription_id = await bus.subscribe_persistent(
    event_types=["asset.discovered"],
    consumer_group="asset-processors",
    consumer_name="worker-1",
    handler=subscriber,
    batch_size=10,
    max_retries=3
)
```

### 4. Event Versioning

Mark events with versions:

```python
from alicemultiverse.events.versioning import versioned_event

@versioned_event(version=2, event_type="asset.discovered", description="Added tags field")
class AssetDiscoveredEventV2(BaseEvent):
    tags: List[str] = field(default_factory=list)
    # ... other fields
```

Events are automatically migrated to current version when consumed.

## Migration Strategy

### Phase 1: Add Persistence (No Breaking Changes)

1. **Update imports** to use EnhancedEventBus:
   ```python
   # from alicemultiverse.events.base import EventBus
   from alicemultiverse.events.enhanced_bus import EnhancedEventBus as EventBus
   ```

2. **Initialize the bus** before use:
   ```python
   bus = EventBus()
   await bus.initialize()  # Add this
   ```

3. **Continue using existing subscribers** - they work unchanged

### Phase 2: Enable Persistent Delivery

1. **Convert critical consumers** to persistent subscriptions:
   ```python
   # Asset processor that must not miss events
   await bus.subscribe_persistent(
       event_types=["asset.discovered", "asset.processed"],
       consumer_group="critical-processors",
       consumer_name=f"worker-{worker_id}",
       handler=asset_processor
   )
   ```

2. **Monitor dead letter queue**:
   ```python
   # Check for failed events
   dlq_count = await bus.get_pending_events("critical-processors")
   if dlq_count > 0:
       # Investigate and replay if needed
       replayed = await bus.replay_dlq("critical-processors")
   ```

### Phase 3: Add Schema Versioning

1. **Version new event changes**:
   ```python
   # When adding fields or changing structure
   @versioned_event(version=2, event_type="quality.assessed", 
                    description="Added provider tracking")
   class QualityAssessedEventV2(BaseEvent):
       provider: str  # New field
       confidence: float  # New field
       # ... existing fields
   ```

2. **Write migrations** for breaking changes:
   ```python
   from alicemultiverse.events.versioning import EventMigration
   
   class QualityAssessedV1ToV2(EventMigration):
       @property
       def from_version(self) -> int:
           return 1
       
       @property
       def to_version(self) -> int:
           return 2
       
       def migrate(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
           migrated = event_data.copy()
           migrated["provider"] = "brisque"  # Default for v1
           migrated["confidence"] = 0.8
           return migrated
   ```

## Backend Comparison

| Feature | SQLite | Redis | Memory |
|---------|--------|-------|---------|
| Setup Complexity | None | Medium | None |
| Performance | Good | Excellent | Best |
| Persistence | Yes | Yes | No |
| Distributed | No | Yes | No |
| Memory Usage | Low | Medium | High |
| Best For | Single instance | Multi-instance | Testing |

## Code Examples

### Event Replay

```python
# Replay events for debugging or recovery
replayed = await bus.replay_events(
    event_types=["asset.processed"],
    handler=debug_handler,
    start_time=datetime.now() - timedelta(days=1),
    limit=100
)
```

### Consumer Groups

```python
# Multiple workers processing same queue
for i in range(3):
    await bus.subscribe_persistent(
        event_types=["workflow.started"],
        consumer_group="workflow-executors",
        consumer_name=f"executor-{i}",
        handler=workflow_executor
    )
```

### Monitoring

```python
# Get statistics
stats = await bus.get_stats()
print(f"Total events: {stats['store']['total_events']}")
print(f"Pending: {stats['store']['pending_events']}")
print(f"DLQ: {stats['store']['dlq_events']}")

# Trim old events
trimmed = await bus.trim_old_events(max_age_days=30)
```

## Troubleshooting

### Events Not Persisting

Check initialization:
```python
if not bus._initialized:
    await bus.initialize()
```

### High Memory Usage

Enable trimming:
```python
# Automatic trimming
config = EventStoreConfig(
    max_events=50000,
    trim_interval_hours=6
)
```

### Lost Events

Check dead letter queue:
```python
# List failed events
pending = await bus.store.get_pending_events("my-group")
for event in pending:
    print(f"Failed: {event.event.event_id} - {event.last_error}")
```

## Best Practices

1. **Use consumer groups** for critical processing
2. **Set appropriate retry limits** based on event importance
3. **Monitor DLQ size** and investigate failures
4. **Version events** from the start
5. **Test migrations** thoroughly
6. **Use SQLite for development**, Redis for production
7. **Set reasonable retention periods** to control storage

## Next Steps

- See `examples/advanced/event_persistence_demo.py` for complete examples
- Read ADR-002 for architectural decisions
- Check `tests/unit/test_event_persistence.py` for usage patterns