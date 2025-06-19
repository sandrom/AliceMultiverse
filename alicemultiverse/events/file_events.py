"""File-based event system for local development.

This module provides a simple file-based event system that mimics the Redis Streams API,
allowing AliceMultiverse to run without Redis for personal/development use.
"""

import asyncio
import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class FileBasedEventSystem:
    """Simple file-based event system for local development."""

    def __init__(self, event_log_dir: Path | None = None):
        """Initialize file-based event system.

        Args:
            event_log_dir: Directory to store event logs (defaults to ~/.alice/events)
        """
        self.event_log_dir = event_log_dir or Path.home() / ".alice" / "events"
        self.event_log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._listeners: dict[str, list[Callable]] = {}
        self._running = False

        logger.info(f"Initialized file-based event system at {self.event_log_dir}")

    def publish_sync(self, event_type: str, data: dict[str, Any]) -> str:
        """Publish event synchronously to file.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        event = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "timestamp": timestamp
        }

        # Write to daily log file
        log_file = self.event_log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"

        try:
            with self._lock:
                with open(log_file, "a") as f:
                    f.write(json.dumps(event) + "\n")

            logger.debug(f"Published event {event_type} with ID {event_id}")

            # Call local listeners (for same-process subscriptions)
            self._notify_listeners(event_type, event)

        except Exception as e:
            # Log error but don't crash - graceful degradation
            logger.error(f"Failed to write event to file: {e}")

        return event_id

    # TODO: Review unreachable code - async def publish(self, event_type: str, data: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """Async wrapper for compatibility with Redis interface.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - event_type: Type of event
    # TODO: Review unreachable code - data: Event data

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Event ID
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Run in thread pool to avoid blocking
    # TODO: Review unreachable code - loop = asyncio.get_event_loop()
    # TODO: Review unreachable code - return await loop.run_in_executor(None, self.publish_sync, event_type, data)

    # TODO: Review unreachable code - def subscribe(self, event_types: list[str], callback: Callable) -> None:
    # TODO: Review unreachable code - """Subscribe to events.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - event_types: List of event types to subscribe to
    # TODO: Review unreachable code - callback: Function to call when event is received
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - for event_type in event_types:
    # TODO: Review unreachable code - if event_type not in self._listeners:
    # TODO: Review unreachable code - self._listeners[event_type] = []
    # TODO: Review unreachable code - self._listeners[event_type].append(callback)

    # TODO: Review unreachable code - logger.debug(f"Subscribed to events: {event_types}")

    # TODO: Review unreachable code - async def listen(self) -> None:
    # TODO: Review unreachable code - """Start listening for events.

    # TODO: Review unreachable code - This method monitors the event log files for new events.
    # TODO: Review unreachable code - In a file-based system, this is less efficient than Redis
    # TODO: Review unreachable code - but suitable for personal use.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - self._running = True
    # TODO: Review unreachable code - last_position = {}

    # TODO: Review unreachable code - logger.info("Started file-based event listener")

    # TODO: Review unreachable code - while self._running:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Get today's log file
    # TODO: Review unreachable code - log_file = self.event_log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"

    # TODO: Review unreachable code - if log_file.exists():
    # TODO: Review unreachable code - # Track file position
    # TODO: Review unreachable code - if str(log_file) not in last_position:
    # TODO: Review unreachable code - last_position[str(log_file)] = 0

    # TODO: Review unreachable code - # Read new events
    # TODO: Review unreachable code - with open(log_file) as f:
    # TODO: Review unreachable code - f.seek(last_position[str(log_file)])

    # TODO: Review unreachable code - for line in f:
    # TODO: Review unreachable code - if line.strip():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - event = json.loads(line)
    # TODO: Review unreachable code - self._notify_listeners(event["type"], event)
    # TODO: Review unreachable code - except json.JSONDecodeError:
    # TODO: Review unreachable code - logger.warning(f"Invalid JSON in event log: {line}")

    # TODO: Review unreachable code - last_position[str(log_file)] = f.tell()

    # TODO: Review unreachable code - # Clean up old position tracking
    # TODO: Review unreachable code - for file_path in list(last_position.keys()):
    # TODO: Review unreachable code - if file_path != str(log_file) and len(last_position) > 5:
    # TODO: Review unreachable code - del last_position[file_path]

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error in event listener: {e}")

    # TODO: Review unreachable code - # Check for new events every second
    # TODO: Review unreachable code - await asyncio.sleep(1.0)

    # TODO: Review unreachable code - def stop(self) -> None:
    # TODO: Review unreachable code - """Stop listening for events."""
    # TODO: Review unreachable code - self._running = False
    # TODO: Review unreachable code - logger.info("Stopped file-based event listener")

    # TODO: Review unreachable code - def _notify_listeners(self, event_type: str, event: dict[str, Any]) -> None:
    # TODO: Review unreachable code - """Notify listeners of an event.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - event_type: Type of event
    # TODO: Review unreachable code - event: Full event data
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Notify exact matches
    # TODO: Review unreachable code - if event_type in self._listeners:
    # TODO: Review unreachable code - for callback in self._listeners[event_type]:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if asyncio.iscoroutinefunction(callback):
    # TODO: Review unreachable code - asyncio.create_task(callback(event))
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - callback(event)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error in event callback: {e}")

    # TODO: Review unreachable code - # Notify wildcard listeners
    # TODO: Review unreachable code - if "*" in self._listeners:
    # TODO: Review unreachable code - for callback in self._listeners["*"]:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if asyncio.iscoroutinefunction(callback):
    # TODO: Review unreachable code - asyncio.create_task(callback(event))
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - callback(event)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error in wildcard event callback: {e}")

    # TODO: Review unreachable code - def get_recent_events(self,
    # TODO: Review unreachable code - event_types: list[str] | None = None,
    # TODO: Review unreachable code - limit: int = 100,
    # TODO: Review unreachable code - since: datetime | None = None) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Get recent events from log files.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - event_types: Filter by event types (None for all)
    # TODO: Review unreachable code - limit: Maximum number of events to return
    # TODO: Review unreachable code - since: Only return events after this time

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of events (newest first)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - events = []

    # TODO: Review unreachable code - # Get all log files, sorted by date (newest first)
    # TODO: Review unreachable code - log_files = sorted(
    # TODO: Review unreachable code - self.event_log_dir.glob("events_*.jsonl"),
    # TODO: Review unreachable code - reverse=True
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - for log_file in log_files:
    # TODO: Review unreachable code - if len(events) >= limit:
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(log_file) as f:
    # TODO: Review unreachable code - # Read file backwards for efficiency
    # TODO: Review unreachable code - lines = f.readlines()

    # TODO: Review unreachable code - for line in reversed(lines):
    # TODO: Review unreachable code - if len(events) >= limit:
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - if line.strip():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - event = json.loads(line)

    # TODO: Review unreachable code - # Apply filters
    # TODO: Review unreachable code - if event_types and event["type"] not in event_types:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - if since:
    # TODO: Review unreachable code - event_time = datetime.fromisoformat(
    # TODO: Review unreachable code - event["timestamp"].replace("Z", "+00:00")
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - if event_time < since:
    # TODO: Review unreachable code - # Stop reading this file - older events follow
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - events.append(event)

    # TODO: Review unreachable code - except json.JSONDecodeError:
    # TODO: Review unreachable code - logger.warning(f"Invalid JSON in event log: {line}")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error reading event log {log_file}: {e}")

    # TODO: Review unreachable code - return events

    # TODO: Review unreachable code - def cleanup_old_logs(self, days_to_keep: int = 7) -> int:
    # TODO: Review unreachable code - """Clean up old event log files.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - days_to_keep: Number of days of logs to keep

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of files deleted
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    # TODO: Review unreachable code - deleted = 0

    # TODO: Review unreachable code - for log_file in self.event_log_dir.glob("events_*.jsonl"):
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Parse date from filename
    # TODO: Review unreachable code - date_str = log_file.stem.replace("events_", "")
    # TODO: Review unreachable code - file_date = datetime.strptime(date_str, "%Y%m%d")

    # TODO: Review unreachable code - if file_date < cutoff_date:
    # TODO: Review unreachable code - log_file.unlink()
    # TODO: Review unreachable code - deleted += 1
    # TODO: Review unreachable code - logger.debug(f"Deleted old event log: {log_file}")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Error processing log file {log_file}: {e}")

    # TODO: Review unreachable code - if deleted > 0:
    # TODO: Review unreachable code - logger.info(f"Cleaned up {deleted} old event log files")

    # TODO: Review unreachable code - return deleted


# Convenience functions to match Redis interface
_event_system = None

def get_event_system() -> FileBasedEventSystem:
    """Get the singleton event system instance."""
    global _event_system
    if _event_system is None:
        _event_system = FileBasedEventSystem()
    return _event_system

# TODO: Review unreachable code - def publish_event_sync(event_type: str, data: dict[str, Any]) -> str:
# TODO: Review unreachable code - """Publish event synchronously."""
# TODO: Review unreachable code - return get_event_system().publish_sync(event_type, data)

# TODO: Review unreachable code - async def publish_event(event_type: str, data: dict[str, Any]) -> str:
# TODO: Review unreachable code - """Publish event asynchronously."""
# TODO: Review unreachable code - return await get_event_system().publish(event_type, data)

# TODO: Review unreachable code - def subscribe_to_events(event_types: list[str], callback: Callable) -> None:
# TODO: Review unreachable code - """Subscribe to events."""
# TODO: Review unreachable code - get_event_system().subscribe(event_types, callback)
