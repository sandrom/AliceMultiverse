"""Migration utilities for transitioning to PostgreSQL events.

This module provides compatibility shims and helpers for migrating
from the old EventBus system to the new PostgreSQL-native events.
"""

import logging
from typing import Any, Dict, Optional

from .postgres_events import get_event_system

logger = logging.getLogger(__name__)


class EventBusCompat:
    """Compatibility wrapper that mimics old EventBus interface.
    
    This allows gradual migration by providing the same API but
    using PostgreSQL events underneath.
    """
    
    def __init__(self):
        """Initialize compatibility wrapper."""
        self.event_system = get_event_system()
        
    async def publish(self, event: Any) -> None:
        """Publish event asynchronously (old interface).
        
        Args:
            event: Event object with type and data attributes
        """
        # Extract event type and data from old event objects
        if hasattr(event, "__class__"):
            event_type = event.__class__.__name__
        else:
            event_type = str(type(event).__name__)
            
        # Convert event to dict
        if hasattr(event, "to_dict"):
            data = event.to_dict()
        elif hasattr(event, "__dict__"):
            data = event.__dict__.copy()
        else:
            data = {"event": str(event)}
            
        # Remove internal attributes
        data = {k: v for k, v in data.items() if not k.startswith("_")}
        
        # Publish using new system
        await self.event_system.publish_async(event_type, data)
    
    def publish_sync(self, event: Any) -> None:
        """Publish event synchronously.
        
        Args:
            event: Event object
        """
        # Extract event type and data
        if hasattr(event, "__class__"):
            event_type = event.__class__.__name__
        else:
            event_type = str(type(event).__name__)
            
        # Convert to dict
        if hasattr(event, "to_dict"):
            data = event.to_dict()
        elif hasattr(event, "__dict__"):
            data = event.__dict__.copy()
        else:
            data = {"event": str(event)}
            
        # Remove internal attributes
        data = {k: v for k, v in data.items() if not k.startswith("_")}
        
        # Publish using new system
        self.event_system.publish(event_type, data)


# Global instance for easy migration
_compat_bus: Optional[EventBusCompat] = None


def get_event_bus() -> EventBusCompat:
    """Get compatibility event bus.
    
    Returns:
        EventBusCompat instance that mimics old EventBus interface
    """
    global _compat_bus
    if _compat_bus is None:
        _compat_bus = EventBusCompat()
    return _compat_bus


# Compatibility function to match old create_event pattern
def create_event(event_class: type, **kwargs) -> Dict[str, Any]:
    """Create event dict in old style.
    
    Args:
        event_class: Event class (used for type name)
        **kwargs: Event data
        
    Returns:
        Dict with event type and data
    """
    return {
        "_type": event_class.__name__,
        **kwargs
    }


# Direct publishing functions for migration
def publish_event_sync(event_type: str, **data) -> str:
    """Publish event synchronously using new system.
    
    Args:
        event_type: Event type (e.g., "asset.processed")
        **data: Event data as keyword arguments
        
    Returns:
        Event ID
    """
    return get_event_system().publish(event_type, data)


async def publish_event_async(event_type: str, **data) -> str:
    """Publish event asynchronously using new system.
    
    Args:
        event_type: Event type
        **data: Event data
        
    Returns:
        Event ID
    """
    return await get_event_system().publish_async(event_type, data)