"""Enhanced event bus with persistence support.

This module extends the base event system to automatically persist events
to Redis Streams when enabled.
"""

import asyncio
import logging

from .base_v2 import BaseEvent, EventBus, EventSubscriber
from .persistence import EventPersistence, get_persistence

logger = logging.getLogger(__name__)


class PersistentEventBus(EventBus):
    """Event bus with automatic persistence to Redis Streams."""

    def __init__(self, persistence: EventPersistence | None = None, persist_events: bool = True):
        """Initialize persistent event bus.

        Args:
            persistence: EventPersistence instance (creates default if None)
            persist_events: Whether to automatically persist events
        """
        super().__init__()
        self.persistence = persistence
        self.persist_events = persist_events
        self._persistence_task = None

    async def initialize(self, redis_url: str | None = None):
        """Initialize persistence layer."""
        if self.persist_events and not self.persistence:
            self.persistence = await get_persistence(redis_url)

    async def publish(self, event: BaseEvent):
        """Publish event and persist to Redis if enabled."""
        # Persist first for reliability
        if self.persist_events and self.persistence:
            try:
                await self.persistence.persist_event(event)
                logger.debug(f"Persisted {event.event_type} event {event.event_id}")
            except Exception as e:
                logger.error(f"Failed to persist event {event.event_id}: {e}")
                # Continue with in-memory publishing even if persistence fails

        # Then publish to in-memory subscribers
        await super().publish(event)

    async def replay_events(
        self, event_type: str, start: str = "-", end: str = "+", count: int | None = None
    ):
        """Replay historical events from persistence.

        Args:
            event_type: Type of events to replay
            start: Start ID or timestamp
            end: End ID or timestamp
            count: Maximum number of events
        """
        if not self.persistence:
            logger.warning("No persistence layer available for replay")
            return

        events = await self.persistence.get_events(event_type, start=start, end=end, count=count)

        for event_data in events:
            # Reconstruct event from data
            # Note: In production, you'd deserialize to proper event class
            await self._notify_subscribers(event_data["event"])

    async def start_consumer(
        self, event_types: list[str], consumer_name: str, subscriber: EventSubscriber
    ):
        """Start consuming events from Redis Streams.

        Args:
            event_types: Event types to consume
            consumer_name: Name of this consumer
            subscriber: Subscriber to handle events
        """
        if not self.persistence:
            logger.warning("No persistence layer available for consumer")
            return

        async def consume():
            """Consumer loop."""
            try:
                async for event_data in self.persistence.consume_events(event_types, consumer_name):
                    try:
                        # Handle event
                        await subscriber.handle_event(event_data["event"])
                        # Acknowledge
                        await event_data["ack"]()
                    except Exception as e:
                        logger.error(f"Error handling consumed event: {e}")
            except asyncio.CancelledError:
                logger.info(f"Consumer {consumer_name} stopped")
                raise

        # Start consumer task
        self._persistence_task = asyncio.create_task(consume())

    async def stop_consumer(self):
        """Stop the consumer task."""
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass
            self._persistence_task = None

    async def close(self):
        """Close the event bus and persistence connections."""
        await self.stop_consumer()
        if self.persistence:
            await self.persistence.disconnect()


# Create global persistent event bus
persistent_event_bus = PersistentEventBus()


async def publish_persistent_event(event: BaseEvent):
    """Helper to publish event with persistence."""
    if not persistent_event_bus.persistence:
        await persistent_event_bus.initialize()
    await persistent_event_bus.publish(event)


# Example usage in event monitor
async def monitor_events_from_redis(event_types: list[str] = None):
    """Monitor events from Redis Streams in real-time."""
    if event_types is None:
        event_types = ["*"]  # All event types

    # Create monitoring subscriber
    class MonitorSubscriber(EventSubscriber):
        async def handle_event(self, event: BaseEvent):
            print(f"[{event.timestamp}] {event.event_type}: {event.event_id}")

    monitor = MonitorSubscriber(event_types=event_types)

    # Initialize persistence
    await persistent_event_bus.initialize()

    # Start consuming
    await persistent_event_bus.start_consumer(event_types, "event-monitor", monitor)

    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        await persistent_event_bus.stop_consumer()
