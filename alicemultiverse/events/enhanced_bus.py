"""Enhanced event bus with integrated persistence and versioning.

This module provides a production-ready event bus that combines
in-memory pub/sub with persistent storage and schema versioning.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from .base import BaseEvent, EventBus, EventSubscriber
from .store import ConsumerConfig, EventFilter, EventStore, EventStoreConfig, create_event_store
from .versioning import EventVersionRegistry, get_version_registry

logger = logging.getLogger(__name__)


class EnhancedEventBus(EventBus):
    """Enhanced event bus with persistence, versioning, and recovery."""
    
    def __init__(
        self,
        store: Optional[EventStore] = None,
        version_registry: Optional[EventVersionRegistry] = None,
        persist_events: bool = True,
        auto_migrate: bool = True
    ):
        """Initialize enhanced event bus.
        
        Args:
            store: Event store instance (creates default if None)
            version_registry: Version registry (uses global if None)
            persist_events: Whether to persist events
            auto_migrate: Whether to auto-migrate events to current version
        """
        super().__init__()
        self.store = store
        self.version_registry = version_registry or get_version_registry()
        self.persist_events = persist_events
        self.auto_migrate = auto_migrate
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
        
    async def initialize(self, config: Optional[EventStoreConfig] = None):
        """Initialize the event bus and persistence layer.
        
        Args:
            config: Event store configuration
        """
        if self._initialized:
            return
            
        # Create store if not provided
        if self.persist_events and not self.store:
            if config is None:
                config = EventStoreConfig.from_env()
                
            self.store = create_event_store(
                config.backend,
                redis_url=config.redis_url,
                db_path=config.sqlite_path,
                max_events=config.max_events
            )
            
        # Connect to store
        if self.store:
            await self.store.connect()
            logger.info(f"Connected to {config.backend if config else 'provided'} event store")
            
        self._initialized = True
        
    async def publish(self, event: BaseEvent):
        """Publish event with persistence and versioning.
        
        Args:
            event: Event to publish
        """
        # Ensure event has current version
        event_data = event.to_dict()
        event_type = event_data.get("event_type", event.__class__.__name__)
        
        # Set version if not present
        if "version" not in event_data:
            current_version = self.version_registry.get_current_version(event_type)
            event_data["version"] = current_version
            
        # Persist first if enabled
        if self.persist_events and self.store:
            try:
                stream_id = await self.store.append(event)
                logger.debug(f"Persisted {event_type} event {event.event_id} as {stream_id}")
            except Exception as e:
                logger.error(f"Failed to persist event {event.event_id}: {e}")
                # Continue with in-memory publishing even if persistence fails
                
        # Then publish to in-memory subscribers
        await super().publish(event)
        
    async def subscribe_persistent(
        self,
        event_types: List[str],
        consumer_group: str,
        consumer_name: str,
        handler: EventSubscriber,
        batch_size: int = 10,
        max_retries: int = 3
    ) -> str:
        """Subscribe to events with persistent delivery guarantees.
        
        Args:
            event_types: Event types to subscribe to
            consumer_group: Consumer group name
            consumer_name: Unique consumer name
            handler: Event handler
            batch_size: Events per batch
            max_retries: Max retries before DLQ
            
        Returns:
            Subscription ID that can be used to unsubscribe
        """
        if not self.store:
            raise RuntimeError("Persistent subscription requires event store")
            
        # Create consumer config
        config = ConsumerConfig(
            consumer_group=consumer_group,
            consumer_name=consumer_name,
            event_types=event_types,
            batch_size=batch_size,
            max_retries=max_retries
        )
        
        # Create handler wrapper
        async def handle_consumed_event(consumed_event):
            try:
                # Get event data and possibly migrate
                event_data = consumed_event.event.event_data
                
                if self.auto_migrate:
                    event_data = self.version_registry.migrate_event(event_data)
                    
                # Let handler process the event
                await handler.handle_event(BaseEvent(**event_data))
                
                # Acknowledge success
                await consumed_event.ack.ack()
                
            except Exception as e:
                logger.error(f"Handler error: {e}")
                # Let the store handle retry/DLQ logic
                raise
                
        # Start subscription
        task = await self.store.subscribe(config, handle_consumed_event)
        
        # Track task
        subscription_id = f"{consumer_group}:{consumer_name}"
        self._consumer_tasks[subscription_id] = task
        
        logger.info(
            f"Started persistent subscription {subscription_id} "
            f"for events {event_types}"
        )
        
        return subscription_id
        
    async def unsubscribe_persistent(self, subscription_id: str):
        """Stop a persistent subscription.
        
        Args:
            subscription_id: ID returned by subscribe_persistent
        """
        if subscription_id in self._consumer_tasks:
            task = self._consumer_tasks[subscription_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
                
            del self._consumer_tasks[subscription_id]
            logger.info(f"Stopped persistent subscription {subscription_id}")
            
    async def replay_events(
        self,
        event_types: List[str],
        handler: EventSubscriber,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
        limit: Optional[int] = None
    ) -> int:
        """Replay historical events.
        
        Args:
            event_types: Event types to replay
            handler: Event handler
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum events to replay
            
        Returns:
            Number of events replayed
        """
        if not self.store:
            logger.warning("No event store available for replay")
            return 0
            
        # Create filter
        filter = EventFilter(
            event_types=event_types,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # Query events
        events = await self.store.query(filter)
        
        # Replay each event
        replayed = 0
        for stored_event in events:
            try:
                # Get event data and possibly migrate
                event_data = stored_event.event_data
                
                if self.auto_migrate:
                    event_data = self.version_registry.migrate_event(event_data)
                    
                # Let handler process the event
                await handler.handle_event(BaseEvent(**event_data))
                replayed += 1
                
            except Exception as e:
                logger.error(f"Error replaying event {stored_event.event_id}: {e}")
                
        logger.info(f"Replayed {replayed} events")
        return replayed
        
    async def get_pending_events(self, consumer_group: str) -> int:
        """Get count of pending events for a consumer group.
        
        Args:
            consumer_group: Consumer group name
            
        Returns:
            Number of pending events
        """
        if not self.store:
            return 0
            
        pending = await self.store.get_pending_events(consumer_group)
        return len(pending)
        
    async def replay_dlq(
        self,
        consumer_group: str,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Replay events from dead letter queue.
        
        Args:
            consumer_group: Consumer group name
            event_types: Optional filter by event types
            
        Returns:
            Number of events replayed
        """
        if not self.store:
            return 0
            
        return await self.store.replay_dlq(consumer_group, event_types)
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics.
        
        Returns:
            Statistics including subscriber counts and store info
        """
        stats = {
            "subscribers": {},
            "store": None
        }
        
        # Get subscriber counts
        for event_type, subs in self._subscribers.items():
            stats["subscribers"][event_type] = len(subs)
            
        # Get store info
        if self.store:
            stats["store"] = await self.store.get_stream_info()
            
        return stats
        
    async def trim_old_events(
        self,
        max_age_days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Trim old events from storage.
        
        Args:
            max_age_days: Maximum age in days
            event_types: Optional filter by event types
            
        Returns:
            Number of events trimmed
        """
        if not self.store:
            return 0
            
        return await self.store.trim_old_events(max_age_days, event_types)
        
    async def close(self):
        """Close the event bus and clean up resources."""
        # Stop all consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
            
        # Wait for tasks to complete
        if self._consumer_tasks:
            await asyncio.gather(
                *self._consumer_tasks.values(),
                return_exceptions=True
            )
            
        # Close store connection
        if self.store:
            await self.store.disconnect()
            
        self._initialized = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global enhanced event bus instance
_enhanced_bus: Optional[EnhancedEventBus] = None


async def get_enhanced_bus(config: Optional[EventStoreConfig] = None) -> EnhancedEventBus:
    """Get or create global enhanced event bus.
    
    Args:
        config: Event store configuration
        
    Returns:
        Enhanced event bus instance
    """
    global _enhanced_bus
    
    if not _enhanced_bus:
        _enhanced_bus = EnhancedEventBus()
        await _enhanced_bus.initialize(config)
        
    return _enhanced_bus


# Convenience functions
async def publish_event(event: BaseEvent):
    """Publish an event using the global enhanced bus."""
    bus = await get_enhanced_bus()
    await bus.publish(event)


async def subscribe_events(
    event_types: List[str],
    consumer_group: str,
    consumer_name: str,
    handler: EventSubscriber,
    **kwargs
) -> str:
    """Subscribe to events using the global enhanced bus."""
    bus = await get_enhanced_bus()
    return await bus.subscribe_persistent(
        event_types,
        consumer_group,
        consumer_name,
        handler,
        **kwargs
    )