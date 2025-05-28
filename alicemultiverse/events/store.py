"""Event store abstraction for flexible persistence backends.

This module provides a common interface for event persistence that can be
backed by different storage systems (Redis, SQLite, etc.).
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol

from .base import BaseEvent

logger = logging.getLogger(__name__)


@dataclass
class StoredEvent:
    """Represents an event stored in the event store."""
    event_id: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    stream_id: str  # Unique ID from the storage backend
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EventFilter:
    """Filter criteria for querying events."""
    event_types: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    start_id: Optional[str] = None
    end_id: Optional[str] = None
    limit: Optional[int] = None
    source_pattern: Optional[str] = None


@dataclass
class ConsumerConfig:
    """Configuration for event consumers."""
    consumer_group: str
    consumer_name: str
    event_types: List[str]
    batch_size: int = 10
    block_timeout_ms: int = 1000
    max_retries: int = 3
    retry_delay_ms: int = 1000
    dead_letter_after: int = 5  # Move to DLQ after N failures


class EventAcknowledger(Protocol):
    """Protocol for acknowledging processed events."""
    
    async def ack(self) -> None:
        """Acknowledge successful processing."""
        ...
    
    async def nack(self, reason: Optional[str] = None) -> None:
        """Negative acknowledgment with optional reason."""
        ...
    
    async def extend_timeout(self, seconds: int) -> None:
        """Extend processing timeout."""
        ...


@dataclass
class ConsumedEvent:
    """Event consumed from the store with acknowledgment."""
    event: StoredEvent
    ack: EventAcknowledger
    delivery_count: int = 1
    last_error: Optional[str] = None


class EventStore(ABC):
    """Abstract base class for event stores."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the storage backend."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the storage backend."""
        pass
    
    @abstractmethod
    async def append(self, event: BaseEvent) -> str:
        """Append an event to the store.
        
        Args:
            event: Event to store
            
        Returns:
            Unique stream ID for the stored event
        """
        pass
    
    @abstractmethod
    async def get_event(self, stream_id: str) -> Optional[StoredEvent]:
        """Get a single event by its stream ID.
        
        Args:
            stream_id: Unique ID from the storage backend
            
        Returns:
            Stored event or None if not found
        """
        pass
    
    @abstractmethod
    async def query(self, filter: EventFilter) -> List[StoredEvent]:
        """Query events based on filter criteria.
        
        Args:
            filter: Filter criteria
            
        Returns:
            List of matching events
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self, 
        config: ConsumerConfig,
        handler: Callable[[ConsumedEvent], Any]
    ) -> asyncio.Task:
        """Subscribe to events with at-least-once delivery.
        
        Args:
            config: Consumer configuration
            handler: Async function to handle events
            
        Returns:
            Subscription task that can be cancelled
        """
        pass
    
    @abstractmethod
    async def get_pending_events(
        self, 
        consumer_group: str,
        max_idle_ms: int = 60000
    ) -> List[ConsumedEvent]:
        """Get events that have been pending for too long.
        
        Args:
            consumer_group: Consumer group name
            max_idle_ms: Maximum idle time in milliseconds
            
        Returns:
            List of pending events
        """
        pass
    
    @abstractmethod
    async def move_to_dlq(
        self,
        event: ConsumedEvent,
        reason: str
    ) -> None:
        """Move an event to the dead letter queue.
        
        Args:
            event: Event to move
            reason: Reason for moving to DLQ
        """
        pass
    
    @abstractmethod
    async def replay_dlq(
        self,
        consumer_group: str,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Replay events from dead letter queue.
        
        Args:
            consumer_group: Target consumer group
            event_types: Optional filter by event types
            
        Returns:
            Number of events replayed
        """
        pass
    
    @abstractmethod
    async def get_stream_info(self) -> Dict[str, Any]:
        """Get information about the event streams.
        
        Returns:
            Stream statistics and metadata
        """
        pass
    
    @abstractmethod
    async def trim_old_events(
        self,
        max_age_days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Remove events older than specified age.
        
        Args:
            max_age_days: Maximum age in days
            event_types: Optional filter by event types
            
        Returns:
            Number of events removed
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class EventStoreError(Exception):
    """Base exception for event store errors."""
    pass


class ConnectionError(EventStoreError):
    """Failed to connect to storage backend."""
    pass


class AcknowledgmentError(EventStoreError):
    """Failed to acknowledge event."""
    pass


# Factory function to create event stores
def create_event_store(backend: str, **kwargs) -> EventStore:
    """Create an event store for the specified backend.
    
    Args:
        backend: Backend type ('redis', 'sqlite', 'memory')
        **kwargs: Backend-specific configuration
        
    Returns:
        Event store instance
        
    Raises:
        ValueError: If backend is not supported
    """
    if backend == "redis":
        from .redis_store import RedisEventStore
        return RedisEventStore(**kwargs)
    elif backend == "sqlite":
        from .sqlite_store import SQLiteEventStore
        return SQLiteEventStore(**kwargs)
    elif backend == "memory":
        from .memory_store import MemoryEventStore
        return MemoryEventStore(**kwargs)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


# Configuration helper
@dataclass
class EventStoreConfig:
    """Configuration for event store."""
    backend: str = "sqlite"  # Default to SQLite for simplicity
    redis_url: Optional[str] = None
    sqlite_path: Optional[Path] = None
    max_events: int = 100000
    trim_interval_hours: int = 24
    dlq_retry_limit: int = 5
    
    @classmethod
    def from_env(cls) -> "EventStoreConfig":
        """Create configuration from environment variables."""
        import os
        
        backend = os.getenv("EVENT_STORE_BACKEND", "sqlite")
        config = cls(backend=backend)
        
        if backend == "redis":
            config.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        elif backend == "sqlite":
            db_path = os.getenv("EVENT_STORE_PATH", "~/.alicemultiverse/events.db")
            config.sqlite_path = Path(db_path).expanduser()
            
        return config