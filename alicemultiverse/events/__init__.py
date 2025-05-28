"""PostgreSQL-native event system for AliceMultiverse.

This module provides a simple, direct event publishing and subscription
system using PostgreSQL's NOTIFY/LISTEN capabilities.
"""

from .postgres_events import (
    PostgresEventSystem,
    get_event_system,
    publish_event,
    subscribe_to_events,
)

__all__ = [
    "PostgresEventSystem",
    "get_event_system", 
    "publish_event",
    "subscribe_to_events",
]