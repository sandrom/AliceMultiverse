"""Event system for AliceMultiverse.

This module provides event publishing and subscription using Redis Streams
for high-performance, reliable event delivery with consumer groups.
"""

# Import from Redis Streams
from .redis_streams import (
    RedisStreamsEventSystem,
    get_event_system,
    publish_event,
    publish_event_sync,
    subscribe_to_events,
)

__all__ = [
    "RedisStreamsEventSystem",
    "get_event_system", 
    "publish_event",
    "publish_event_sync",
    "subscribe_to_events",
]