"""Base event infrastructure for AliceMultiverse - Version 2.

This version avoids dataclass inheritance issues by using composition
and a builder pattern for events.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import uuid4

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseEvent")


class BaseEvent(ABC):
    """Abstract base class for all events.

    Subclasses should be dataclasses and implement event_type property.
    Common fields are injected via the EventBuilder.
    """

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type identifier."""
        pass

    def with_metadata(
        self,
        event_id: str = None,
        timestamp: datetime = None,
        source: str = "",
        version: str = "1.0.0",
    ) -> "BaseEvent":
        """Add metadata fields to the event.

        This method adds the common event fields without inheritance issues.
        """
        self._event_id = event_id or str(uuid4())
        self._timestamp = timestamp or datetime.now(UTC)
        self._source = source
        self._version = version
        return self

    @property
    def event_id(self) -> str:
        """Get event ID."""
        return getattr(self, "_event_id", str(uuid4()))

    @property
    def timestamp(self) -> datetime:
        """Get timestamp."""
        return getattr(self, "_timestamp", datetime.now(UTC))

    @property
    def source(self) -> str:
        """Get source."""
        return getattr(self, "_source", "")

    @property
    def version(self) -> str:
        """Get version."""
        return getattr(self, "_version", "1.0.0")

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        # Start with dataclass fields
        if hasattr(self, "__dataclass_fields__"):
            data = asdict(self)
        else:
            data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        # Add metadata fields
        data["event_id"] = self.event_id
        data["timestamp"] = self.timestamp.isoformat()
        data["source"] = self.source
        data["version"] = self.version
        data["event_type"] = self.event_type

        return data

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create event from dictionary."""
        data = data.copy()

        # Extract metadata
        metadata = {
            "event_id": data.pop("event_id", None),
            "timestamp": data.pop("timestamp", None),
            "source": data.pop("source", ""),
            "version": data.pop("version", "1.0.0"),
        }

        # Convert timestamp
        if metadata["timestamp"] and isinstance(metadata["timestamp"], str):
            metadata["timestamp"] = datetime.fromisoformat(metadata["timestamp"])

        # Remove event_type as it's a property
        data.pop("event_type", None)

        # Create instance and add metadata
        instance = cls(**data)
        instance.with_metadata(**metadata)

        return instance

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class EventBuilder:
    """Builder for creating events with proper metadata."""

    def __init__(self, event_class: type[BaseEvent]):
        self.event_class = event_class
        self.params = {}
        self.metadata = {}

    def with_params(self, **kwargs) -> "EventBuilder":
        """Set event-specific parameters."""
        self.params.update(kwargs)
        return self

    def with_source(self, source: str) -> "EventBuilder":
        """Set event source."""
        self.metadata["source"] = source
        return self

    def with_timestamp(self, timestamp: datetime) -> "EventBuilder":
        """Set event timestamp."""
        self.metadata["timestamp"] = timestamp
        return self

    def build(self) -> BaseEvent:
        """Build the event instance."""
        event = self.event_class(**self.params)
        event.with_metadata(**self.metadata)
        return event


# Convenience function for creating events
def create_event(event_class: type[BaseEvent], source: str = "", **params) -> BaseEvent:
    """Create an event with metadata.

    Example:
        event = create_event(AssetDiscoveredEvent,
                           source="scanner",
                           file_path="/test.png",
                           content_hash="abc123")
    """
    return EventBuilder(event_class).with_source(source).with_params(**params).build()


class EventSubscriber(ABC):
    """Base class for event subscribers."""

    @abstractmethod
    async def handle_event(self, event: BaseEvent) -> None:
        """Handle an event asynchronously."""
        pass

    @property
    @abstractmethod
    def event_types(self) -> list[str]:
        """Return list of event types this subscriber handles."""
        pass


class EventPublisher(ABC):
    """Abstract base for event publishers."""

    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """Publish an event."""
        pass


class EventBus(EventPublisher):
    """Simple in-memory event bus implementation."""

    def __init__(self):
        self._subscribers: dict[str, list[EventSubscriber]] = {}
        self._middleware: list[Callable[[BaseEvent], None]] = []

    def subscribe(self, subscriber: EventSubscriber) -> None:
        """Register a subscriber for its declared event types."""
        for event_type in subscriber.event_types:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(subscriber)
            logger.debug(f"Subscribed {subscriber.__class__.__name__} to {event_type}")

    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        """Remove a subscriber."""
        for event_type in subscriber.event_types:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    s for s in self._subscribers[event_type] if s != subscriber
                ]

    def add_middleware(self, middleware: Callable[[BaseEvent], None]) -> None:
        """Add middleware that processes all events."""
        self._middleware.append(middleware)

    async def publish(self, event: BaseEvent) -> None:
        """Publish an event to all registered subscribers."""
        # Ensure event has metadata
        if not hasattr(event, "_event_id"):
            event.with_metadata()

        # Run middleware
        for middleware in self._middleware:
            try:
                middleware(event)
            except Exception as e:
                logger.error(f"Middleware error: {e}")

        # Get subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        subscribers.extend(self._subscribers.get("*", []))

        # Notify all subscribers concurrently
        if subscribers:
            tasks = [self._notify_subscriber(subscriber, event) for subscriber in subscribers]
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Published {event.event_type} to {len(subscribers)} subscribers")

    async def _notify_subscriber(self, subscriber: EventSubscriber, event: BaseEvent) -> None:
        """Notify a single subscriber with error handling."""
        try:
            await subscriber.handle_event(event)
        except Exception as e:
            logger.error(
                f"Error in subscriber {subscriber.__class__.__name__} "
                f"handling {event.event_type}: {e}"
            )


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return _event_bus


def set_event_bus(bus: EventBus) -> None:
    """Set a custom event bus implementation."""
    global _event_bus
    _event_bus = bus


async def publish_event(event: BaseEvent) -> None:
    """Publish an event to the global event bus."""
    await _event_bus.publish(event)
