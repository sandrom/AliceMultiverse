"""Event system for AliceMultiverse.

This module provides event publishing and subscription using a simple file-based
system suitable for personal use.
"""

import logging

from .file_events import (
    FileBasedEventSystem,
    get_event_system,
    publish_event,
    publish_event_sync,
    subscribe_to_events,
)

logger = logging.getLogger(__name__)

__all__ = [
    "FileBasedEventSystem",
    "get_event_system",
    "publish_event",
    "publish_event_sync",
    "subscribe_to_events",
]
