"""File-based event system for local development.

This module provides a simple file-based event system that mimics the Redis Streams API,
allowing AliceMultiverse to run without Redis for personal/development use.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class FileBasedEventSystem:
    """Simple file-based event system for local development."""
    
    def __init__(self, event_log_dir: Optional[Path] = None):
        """Initialize file-based event system.
        
        Args:
            event_log_dir: Directory to store event logs (defaults to ~/.alice/events)
        """
        self.event_log_dir = event_log_dir or Path.home() / ".alice" / "events"
        self.event_log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._listeners: Dict[str, List[Callable]] = {}
        self._running = False
        
        logger.info(f"Initialized file-based event system at {self.event_log_dir}")
    
    def publish_sync(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish event synchronously to file.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
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
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """Async wrapper for compatibility with Redis interface.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Event ID
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.publish_sync, event_type, data)
    
    def subscribe(self, event_types: List[str], callback: Callable) -> None:
        """Subscribe to events.
        
        Args:
            event_types: List of event types to subscribe to
            callback: Function to call when event is received
        """
        for event_type in event_types:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)
            
        logger.debug(f"Subscribed to events: {event_types}")
    
    async def listen(self) -> None:
        """Start listening for events.
        
        This method monitors the event log files for new events.
        In a file-based system, this is less efficient than Redis
        but suitable for personal use.
        """
        self._running = True
        last_position = {}
        
        logger.info("Started file-based event listener")
        
        while self._running:
            try:
                # Get today's log file
                log_file = self.event_log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
                
                if log_file.exists():
                    # Track file position
                    if str(log_file) not in last_position:
                        last_position[str(log_file)] = 0
                    
                    # Read new events
                    with open(log_file, "r") as f:
                        f.seek(last_position[str(log_file)])
                        
                        for line in f:
                            if line.strip():
                                try:
                                    event = json.loads(line)
                                    self._notify_listeners(event["type"], event)
                                except json.JSONDecodeError:
                                    logger.warning(f"Invalid JSON in event log: {line}")
                        
                        last_position[str(log_file)] = f.tell()
                
                # Clean up old position tracking
                for file_path in list(last_position.keys()):
                    if file_path != str(log_file) and len(last_position) > 5:
                        del last_position[file_path]
                
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
            
            # Check for new events every second
            await asyncio.sleep(1.0)
    
    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False
        logger.info("Stopped file-based event listener")
    
    def _notify_listeners(self, event_type: str, event: Dict[str, Any]) -> None:
        """Notify listeners of an event.
        
        Args:
            event_type: Type of event
            event: Full event data
        """
        # Notify exact matches
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
        
        # Notify wildcard listeners
        if "*" in self._listeners:
            for callback in self._listeners["*"]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in wildcard event callback: {e}")
    
    def get_recent_events(self, 
                         event_types: Optional[List[str]] = None,
                         limit: int = 100,
                         since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get recent events from log files.
        
        Args:
            event_types: Filter by event types (None for all)
            limit: Maximum number of events to return
            since: Only return events after this time
            
        Returns:
            List of events (newest first)
        """
        events = []
        
        # Get all log files, sorted by date (newest first)
        log_files = sorted(
            self.event_log_dir.glob("events_*.jsonl"),
            reverse=True
        )
        
        for log_file in log_files:
            if len(events) >= limit:
                break
                
            try:
                with open(log_file, "r") as f:
                    # Read file backwards for efficiency
                    lines = f.readlines()
                    
                    for line in reversed(lines):
                        if len(events) >= limit:
                            break
                            
                        if line.strip():
                            try:
                                event = json.loads(line)
                                
                                # Apply filters
                                if event_types and event["type"] not in event_types:
                                    continue
                                    
                                if since:
                                    event_time = datetime.fromisoformat(
                                        event["timestamp"].replace("Z", "+00:00")
                                    )
                                    if event_time < since:
                                        # Stop reading this file - older events follow
                                        break
                                
                                events.append(event)
                                
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in event log: {line}")
                                
            except Exception as e:
                logger.error(f"Error reading event log {log_file}: {e}")
        
        return events
    
    def cleanup_old_logs(self, days_to_keep: int = 7) -> int:
        """Clean up old event log files.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted = 0
        
        for log_file in self.event_log_dir.glob("events_*.jsonl"):
            try:
                # Parse date from filename
                date_str = log_file.stem.replace("events_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted += 1
                    logger.debug(f"Deleted old event log: {log_file}")
                    
            except Exception as e:
                logger.warning(f"Error processing log file {log_file}: {e}")
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old event log files")
            
        return deleted


# Convenience functions to match Redis interface
_event_system = None

def get_event_system() -> FileBasedEventSystem:
    """Get the singleton event system instance."""
    global _event_system
    if _event_system is None:
        _event_system = FileBasedEventSystem()
    return _event_system

def publish_event_sync(event_type: str, data: Dict[str, Any]) -> str:
    """Publish event synchronously."""
    return get_event_system().publish_sync(event_type, data)

async def publish_event(event_type: str, data: Dict[str, Any]) -> str:
    """Publish event asynchronously."""
    return await get_event_system().publish(event_type, data)

def subscribe_to_events(event_types: List[str], callback: Callable) -> None:
    """Subscribe to events."""
    get_event_system().subscribe(event_types, callback)