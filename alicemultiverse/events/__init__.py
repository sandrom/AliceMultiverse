"""Event system for AliceMultiverse.

This module provides event publishing and subscription using Redis Streams
for high-performance, reliable event delivery with consumer groups.

Migration from PostgreSQL:
- PostgresEventSystem -> RedisStreamsEventSystem
- publish_event() now returns a coroutine (use await)
- For sync contexts, use publish_event_sync()
"""

# Import from Redis Streams (new default)
from .redis_streams import (
    RedisStreamsEventSystem,
    get_event_system,
    publish_event,
    publish_event_sync,
    subscribe_to_events,
)

# Keep PostgreSQL imports available for migration
from .postgres_events import (
    PostgresEventSystem,
    get_event_system as get_postgres_event_system,
    publish_event as publish_postgres_event,
    subscribe_to_events as subscribe_to_postgres_events,
)

__all__ = [
    # Redis Streams (new default)
    "RedisStreamsEventSystem",
    "get_event_system", 
    "publish_event",
    "publish_event_sync",
    "subscribe_to_events",
    # PostgreSQL (deprecated)
    "PostgresEventSystem",
    "get_postgres_event_system",
    "publish_postgres_event",
    "subscribe_to_postgres_events",
]