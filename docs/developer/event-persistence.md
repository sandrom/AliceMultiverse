# Event Persistence with Redis Streams

## Overview

AliceMultiverse includes an optional event persistence layer using Redis Streams. This enables:
- Reliable event storage and delivery
- Event replay for debugging and recovery
- Consumer groups for distributed processing
- Event sourcing patterns

## Installation

Redis is an optional dependency. Install it when you need event persistence:

```bash
pip install redis>=5.0.0
```

You'll also need a Redis server running:

```bash
# macOS
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

## Configuration

### Basic Setup

```python
from alicemultiverse.events.persistence import EventPersistence

# Create persistence instance
persistence = EventPersistence(
    redis_url="redis://localhost:6379",
    stream_prefix="alice:events:",
    consumer_group="alice-main",
    max_len=100000  # Max events per stream
)

# Connect
await persistence.connect()
```

### Using the Persistent Event Bus

```python
from alicemultiverse.events.base_v2_persistence import PersistentEventBus

# Create bus with persistence enabled
bus = PersistentEventBus(persist_events=True)
await bus.initialize()

# Publish events - automatically persisted
await bus.publish(event)
```

## Features

### 1. Event Storage

Events are stored in Redis Streams with:
- Type-specific streams (e.g., `alice:events:asset.discovered`)
- Global stream for monitoring all events
- Automatic FIFO eviction when max length reached

### 2. Event Retrieval

```python
# Get recent events
events = await persistence.get_events(
    "asset.discovered",
    count=100
)

# Get events in time range
events = await persistence.get_events(
    "asset.discovered",
    start="1234567890-0",  # Stream ID
    end="+"  # Latest
)
```

### 3. Consumer Groups

Consume events with at-least-once delivery:

```python
# Create consumer
async for event_data in persistence.consume_events(
    ["asset.discovered", "asset.processed"],
    consumer_name="worker-1"
):
    # Process event
    await process_event(event_data["event"])
    
    # Acknowledge when done
    await event_data["ack"]()
```

### 4. Pending Event Recovery

Handle failed/stuck events:

```python
# Get pending events older than 60 seconds
pending = await persistence.get_pending_events(
    "asset.discovered",
    idle_ms=60000
)

# Reprocess them
for event in pending:
    await process_event(event["event"])
```

### 5. Event Replay

Replay historical events:

```python
# Replay events to subscribers
await bus.replay_events(
    "asset.discovered",
    start="-",  # Beginning
    count=1000
)
```

## Monitoring

### Stream Information

```python
# Get stream stats
info = await persistence.get_stream_info("asset.discovered")
print(f"Events in stream: {info['length']}")
print(f"Consumer groups: {info['consumer_groups']}")
```

### Event Monitor Script

The project includes an event monitor that can consume from Redis:

```python
from alicemultiverse.events.base_v2_persistence import monitor_events_from_redis

# Monitor all events
await monitor_events_from_redis()

# Monitor specific types
await monitor_events_from_redis(["asset.discovered", "workflow.started"])
```

## Best Practices

### 1. Error Handling

Always handle persistence failures gracefully:

```python
try:
    await persistence.persist_event(event)
except Exception as e:
    logger.error(f"Failed to persist: {e}")
    # Continue processing - don't lose the event
```

### 2. Consumer Design

- Use meaningful consumer names
- Implement idempotent event handlers
- Set appropriate idle timeouts for pending recovery
- Monitor consumer lag

### 3. Stream Management

- Set reasonable max lengths to prevent unbounded growth
- Implement periodic trimming for old events
- Use time-based trimming for compliance

```python
# Trim events older than 30 days
await persistence.trim_old_events("asset.discovered", max_age_days=30)
```

### 4. Testing

The persistence layer includes comprehensive mocking for tests:

```python
# Tests automatically skip if Redis not installed
pytest tests/unit/test_event_persistence.py

# Integration tests with real Redis
pytest tests/integration/test_event_persistence_redis.py
```

## Architecture Notes

### Stream Structure

- **Type-specific streams**: Efficient consumption by event type
- **Global stream**: Complete audit trail and monitoring
- **Consumer groups**: Enable horizontal scaling

### Performance Considerations

- Redis Streams are very efficient (millions of events/second)
- Use `MAXLEN` with approximation for better performance
- Consider partitioning for extreme scale

### Future Enhancements

- Dapr integration for multi-backend support
- Kafka adapter for enterprise deployments
- Event compaction and archival strategies