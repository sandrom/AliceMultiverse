"""Event system for AliceMultiverse.

This module provides event publishing and subscription with support for both:
- Redis Streams for distributed, high-performance event delivery
- File-based events for local development and personal use

The system automatically selects the appropriate backend based on configuration.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Check if Redis events are enabled (default to file-based for simplicity)
USE_REDIS = os.getenv("USE_REDIS_EVENTS", "false").lower() == "true"

try:
    if USE_REDIS:
        # Try to import Redis-based system
        from .redis_streams import (
            RedisStreamsEventSystem,
            get_event_system,
            publish_event,
            publish_event_sync,
            subscribe_to_events,
        )
        logger.info("Using Redis Streams for events")
    else:
        raise ImportError("File-based events requested")
        
except (ImportError, Exception) as e:
    # Fall back to file-based system
    if USE_REDIS:
        logger.warning(f"Failed to initialize Redis events: {e}. Falling back to file-based events.")
    else:
        logger.info("Using file-based event system")
        
    from .file_events import (
        FileBasedEventSystem as RedisStreamsEventSystem,  # Alias for compatibility
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