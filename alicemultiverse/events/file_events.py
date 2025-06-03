"""File-based event system for local development.

A simple, reliable event system that writes to local files instead of Redis.
Perfect for personal tools and development environments.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from threading import Lock

from alicemultiverse.core.structured_logging import get_logger
from alicemultiverse.core.metrics import events_published_total, event_processing_duration_seconds

logger = get_logger(__name__)


class FileBasedEventSystem:
    """Simple file-based event system for local development.
    
    Writes events to JSON Lines files organized by date.
    Provides the same API as RedisStreamsEventSystem for compatibility.
    """
    
    def __init__(self, event_log_dir: Optional[str] = None):
        """Initialize the event system.
        
        Args:
            event_log_dir: Directory for event logs. Defaults to ~/.alice/events
        """
        if event_log_dir:
            self.event_log_dir = Path(event_log_dir)
        else:
            self.event_log_dir = Path.home() / ".alice" / "events"
            
        self.event_log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._listeners: Dict[str, List[Callable]] = {}
        self._running: bool = False
        
        logger.info(f"Initialized file-based event system at {self.event_log_dir}")
        
    def publish_sync(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event synchronously.
        
        Args:
            event_type: Type of event (e.g., "asset.processed")
            data: Event data
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        # Track metrics
        events_published_total.labels(event_type=event_type).inc()
        
        event = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "timestamp": timestamp.isoformat()
        }
        
        # Write to daily log file
        log_file = self.event_log_dir / f"events_{timestamp.strftime('%Y%m%d')}.jsonl"
        
        try:
            with self._lock:
                with open(log_file, "a") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
                    
            logger.debug(f"Published event {event_type} with ID {event_id}")
            
            # Notify local listeners (synchronous)
            self._notify_listeners_sync(event_type, event)
            
            return event_id
            
        except Exception as e:
            # Log error but don't crash - events are not critical
            logger.error(f"Failed to publish event {event_type}: {e}")
            return event_id  # Return ID anyway for compatibility
            
    async def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event asynchronously.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Event ID
        """
        # For file-based system, just wrap the sync version
        return self.publish_sync(event_type, data)
        
    async def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Event type to subscribe to (supports wildcards like "asset.*")
            handler: Function to call when event is received
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}")
        
    async def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from events.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._listeners:
            self._listeners[event_type].remove(handler)
            if not self._listeners[event_type]:
                del self._listeners[event_type]
                
    async def start_listening(self) -> None:
        """Start listening for events (no-op for file-based system)."""
        self._running = True
        logger.info("File-based event system started (local only)")
        
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        self._running = False
        logger.info("File-based event system stopped")
        
    def _notify_listeners_sync(self, event_type: str, event: Dict[str, Any]) -> None:
        """Notify local listeners synchronously."""
        start_time = time.time()
        
        # Exact match
        if event_type in self._listeners:
            for handler in self._listeners[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
                    
        # Wildcard patterns
        for pattern, handlers in self._listeners.items():
            if pattern != event_type and self._matches_pattern(event_type, pattern):
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
                        
        # Record metrics
        duration = time.time() - start_time
        event_processing_duration_seconds.labels(event_type=event_type).observe(duration)
        
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches subscription pattern.
        
        Supports exact matches and wildcards:
        - "asset.processed" matches "asset.processed"
        - "asset.*" matches "asset.processed", "asset.created", etc.
        - "*" matches everything
        """
        if pattern == "*":
            return True
        if pattern == event_type:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + ".")
        return False
        
    async def get_recent_events(
        self, 
        limit: int = 100, 
        event_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent events from log files.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            start_time: Start time filter (ISO format)
            end_time: End time filter (ISO format)
            
        Returns:
            List of events (most recent first)
        """
        events = []
        
        # Get all event log files, sorted by date (newest first)
        log_files = sorted(
            self.event_log_dir.glob("events_*.jsonl"),
            reverse=True
        )
        
        for log_file in log_files:
            if len(events) >= limit:
                break
                
            try:
                with open(log_file, "r") as f:
                    # Read file in reverse order for recent events
                    lines = f.readlines()
                    for line in reversed(lines):
                        if len(events) >= limit:
                            break
                            
                        try:
                            event = json.loads(line.strip())
                            
                            # Apply filters
                            if event_type and event.get("type") != event_type:
                                continue
                                
                            if start_time and event.get("timestamp", "") < start_time:
                                continue
                                
                            if end_time and event.get("timestamp", "") > end_time:
                                continue
                                
                            events.append(event)
                            
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Error reading event log {log_file}: {e}")
                
        return events
        
    async def get_pending_messages(self, event_type: str) -> List[Dict[str, Any]]:
        """Get pending messages (not applicable for file-based system).
        
        Returns empty list for compatibility.
        """
        return []
        
    async def claim_abandoned_messages(self, event_type: str, idle_time_ms: int = 60000) -> int:
        """Claim abandoned messages (not applicable for file-based system).
        
        Returns 0 for compatibility.
        """
        return 0


# Global instance for convenience
_event_system: Optional[FileBasedEventSystem] = None


def get_event_system() -> FileBasedEventSystem:
    """Get the global event system instance."""
    global _event_system
    if _event_system is None:
        _event_system = FileBasedEventSystem()
    return _event_system


# Convenience functions for simple usage
async def publish_event(event_type: str, data: Dict[str, Any]) -> str:
    """Publish an event using the global event system."""
    return await get_event_system().publish(event_type, data)


def publish_event_sync(event_type: str, data: Dict[str, Any]) -> str:
    """Publish an event synchronously using the global event system."""
    return get_event_system().publish_sync(event_type, data)


async def subscribe_to_events(event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """Subscribe to events using the global event system."""
    await get_event_system().subscribe(event_type, handler)