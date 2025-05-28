"""Redis implementation of the event store.

This module adapts the existing Redis Streams persistence to the EventStore interface.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .base import BaseEvent
from .persistence import EventPersistence, REDIS_AVAILABLE
from .store import (
    AcknowledgmentError,
    ConsumedEvent,
    ConsumerConfig,
    EventAcknowledger,
    EventFilter,
    EventStore,
    EventStoreError,
    StoredEvent,
)

logger = logging.getLogger(__name__)


class RedisAcknowledger(EventAcknowledger):
    """Redis-specific event acknowledger."""
    
    def __init__(
        self,
        persistence: EventPersistence,
        stream_key: str,
        consumer_group: str,
        message_id: str,
        event: StoredEvent
    ):
        self.persistence = persistence
        self.stream_key = stream_key
        self.consumer_group = consumer_group
        self.message_id = message_id
        self.event = event
        self._acknowledged = False
        
    async def ack(self) -> None:
        """Acknowledge successful processing."""
        if self._acknowledged:
            return
            
        try:
            await self.persistence._redis.xack(
                self.stream_key, 
                self.consumer_group, 
                self.message_id
            )
            self._acknowledged = True
            logger.debug(f"Acknowledged event {self.event.event_id}")
        except Exception as e:
            raise AcknowledgmentError(f"Failed to acknowledge: {e}")
    
    async def nack(self, reason: Optional[str] = None) -> None:
        """Negative acknowledgment - message will be redelivered."""
        # Redis doesn't have explicit NACK, just don't ACK
        # Log the failure reason
        if reason:
            logger.warning(f"NACK event {self.event.event_id}: {reason}")
    
    async def extend_timeout(self, seconds: int) -> None:
        """Extend processing timeout."""
        # Redis Streams doesn't support extending timeout directly
        # This is a no-op, but could be implemented with XCLAIM
        pass


class RedisEventStore(EventStore):
    """Redis Streams implementation of event store."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        stream_prefix: str = "alice:events:",
        max_len: int = 100000,
        dlq_suffix: str = ":dlq"
    ):
        """Initialize Redis event store.
        
        Args:
            redis_url: Redis connection URL
            stream_prefix: Prefix for stream keys
            max_len: Maximum events per stream
            dlq_suffix: Suffix for dead letter queue streams
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not installed. Install with: pip install redis>=5.0.0")
            
        self.persistence = EventPersistence(
            redis_url=redis_url,
            stream_prefix=stream_prefix,
            max_len=max_len
        )
        self.dlq_suffix = dlq_suffix
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self) -> None:
        """Establish connection to Redis."""
        await self.persistence.connect()
        
    async def disconnect(self) -> None:
        """Close connection to Redis."""
        # Cancel all consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._consumer_tasks:
            await asyncio.gather(
                *self._consumer_tasks.values(),
                return_exceptions=True
            )
            
        await self.persistence.disconnect()
        
    async def append(self, event: BaseEvent) -> str:
        """Append an event to the store."""
        return await self.persistence.persist_event(event)
        
    async def get_event(self, stream_id: str) -> Optional[StoredEvent]:
        """Get a single event by its stream ID."""
        # Parse stream key and entry ID from stream_id
        # Format: "stream_key:entry_id"
        parts = stream_id.split(":", 1)
        if len(parts) != 2:
            return None
            
        stream_key, entry_id = parts
        
        try:
            entries = await self.persistence._redis.xrange(
                stream_key, 
                min=entry_id, 
                max=entry_id, 
                count=1
            )
            
            if not entries:
                return None
                
            entry_id, data = entries[0]
            event_data = json.loads(data["event"])
            
            return StoredEvent(
                event_id=event_data["event_id"],
                event_type=event_data["event_type"],
                event_data=event_data,
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                stream_id=f"{stream_key}:{entry_id}"
            )
        except Exception as e:
            logger.error(f"Failed to get event {stream_id}: {e}")
            return None
            
    async def query(self, filter: EventFilter) -> List[StoredEvent]:
        """Query events based on filter criteria."""
        events = []
        
        # Determine which streams to query
        if filter.event_types:
            stream_keys = [
                self.persistence._get_stream_key(event_type)
                for event_type in filter.event_types
            ]
        else:
            # Query all event types from global stream
            stream_keys = [self.persistence._get_global_stream_key()]
            
        # Convert time filters to Redis IDs if provided
        start = "-"
        end = "+"
        
        if filter.start_time:
            start = str(int(filter.start_time.timestamp() * 1000))
        elif filter.start_id:
            start = filter.start_id
            
        if filter.end_time:
            end = str(int(filter.end_time.timestamp() * 1000))
        elif filter.end_id:
            end = filter.end_id
            
        # Query each stream
        for stream_key in stream_keys:
            try:
                entries = await self.persistence._redis.xrange(
                    stream_key,
                    min=start,
                    max=end,
                    count=filter.limit
                )
                
                for entry_id, data in entries:
                    event_data = json.loads(data.get("event", data.get("data", "{}")))
                    
                    # Apply source pattern filter if specified
                    if filter.source_pattern:
                        source = event_data.get("source", "")
                        if filter.source_pattern not in source:
                            continue
                            
                    events.append(StoredEvent(
                        event_id=event_data["event_id"],
                        event_type=event_data["event_type"],
                        event_data=event_data,
                        timestamp=datetime.fromisoformat(event_data["timestamp"]),
                        stream_id=f"{stream_key}:{entry_id}"
                    ))
                    
                    if filter.limit and len(events) >= filter.limit:
                        return events
                        
            except Exception as e:
                logger.error(f"Failed to query stream {stream_key}: {e}")
                
        return events
        
    async def subscribe(
        self,
        config: ConsumerConfig,
        handler: Callable[[ConsumedEvent], Any]
    ) -> asyncio.Task:
        """Subscribe to events with at-least-once delivery."""
        
        async def consumer_loop():
            """Main consumer loop with error handling and retries."""
            retry_count = 0
            
            while True:
                try:
                    # Consume events
                    async for event_data in self.persistence.consume_events(
                        event_types=config.event_types,
                        consumer_name=config.consumer_name,
                        block_ms=config.block_timeout_ms,
                        count=config.batch_size
                    ):
                        # Parse event
                        stream_key = event_data["stream_key"]
                        message_id = event_data["message_id"]
                        event_dict = event_data["event"]
                        
                        # Create stored event
                        stored_event = StoredEvent(
                            event_id=event_dict["event_id"],
                            event_type=event_dict["event_type"],
                            event_data=event_dict,
                            timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                            stream_id=f"{stream_key}:{message_id}"
                        )
                        
                        # Create acknowledger
                        ack = RedisAcknowledger(
                            self.persistence,
                            stream_key,
                            config.consumer_group,
                            message_id,
                            stored_event
                        )
                        
                        # Get delivery count from pending info
                        delivery_count = 1  # Default, would need XPENDING to get actual
                        
                        # Create consumed event
                        consumed = ConsumedEvent(
                            event=stored_event,
                            ack=ack,
                            delivery_count=delivery_count
                        )
                        
                        # Handle event with retry logic
                        try:
                            await handler(consumed)
                            retry_count = 0  # Reset on success
                        except Exception as e:
                            logger.error(f"Handler error for event {stored_event.event_id}: {e}")
                            
                            # Check if should move to DLQ
                            if delivery_count >= config.dead_letter_after:
                                await self.move_to_dlq(consumed, str(e))
                                await ack.ack()  # Remove from main queue
                            else:
                                await ack.nack(str(e))
                                
                except asyncio.CancelledError:
                    logger.info(f"Consumer {config.consumer_name} cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Consumer loop error: {e}")
                    retry_count += 1
                    
                    if retry_count >= config.max_retries:
                        logger.error(f"Max retries reached for consumer {config.consumer_name}")
                        raise EventStoreError(f"Consumer failed after {config.max_retries} retries")
                        
                    # Exponential backoff
                    await asyncio.sleep(config.retry_delay_ms * (2 ** retry_count) / 1000)
                    
        # Create and track task
        task = asyncio.create_task(consumer_loop())
        self._consumer_tasks[config.consumer_name] = task
        return task
        
    async def get_pending_events(
        self,
        consumer_group: str,
        max_idle_ms: int = 60000
    ) -> List[ConsumedEvent]:
        """Get events that have been pending for too long."""
        pending_events = []
        
        # Get all streams for the consumer group
        # This is a limitation - we'd need to track which streams have this group
        # For now, return empty list
        logger.warning("get_pending_events not fully implemented for Redis backend")
        return pending_events
        
    async def move_to_dlq(
        self,
        event: ConsumedEvent,
        reason: str
    ) -> None:
        """Move an event to the dead letter queue."""
        # Create DLQ stream key
        dlq_key = f"{self.persistence.stream_prefix}dlq:{event.event.event_type}"
        
        # Add to DLQ with failure metadata
        dlq_data = {
            "event": json.dumps(event.event.event_data, default=str),
            "original_stream_id": event.event.stream_id,
            "failure_reason": reason,
            "failure_time": datetime.now().isoformat(),
            "delivery_count": str(event.delivery_count)
        }
        
        await self.persistence._redis.xadd(
            dlq_key,
            dlq_data,
            maxlen=self.persistence.max_len,
            approximate=True
        )
        
        logger.info(f"Moved event {event.event.event_id} to DLQ: {reason}")
        
    async def replay_dlq(
        self,
        consumer_group: str,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Replay events from dead letter queue."""
        replayed = 0
        
        # Determine DLQ streams to replay
        if event_types:
            dlq_keys = [
                f"{self.persistence.stream_prefix}dlq:{event_type}"
                for event_type in event_types
            ]
        else:
            # Would need SCAN to find all DLQ streams
            logger.warning("Replaying all DLQ events not implemented")
            return 0
            
        for dlq_key in dlq_keys:
            try:
                # Read all events from DLQ
                entries = await self.persistence._redis.xrange(dlq_key)
                
                for entry_id, data in entries:
                    # Re-add to original stream
                    event_data = json.loads(data["event"])
                    event_type = event_data["event_type"]
                    original_key = self.persistence._get_stream_key(event_type)
                    
                    # Add back to original stream
                    await self.persistence._redis.xadd(
                        original_key,
                        {"event": data["event"]},
                        maxlen=self.persistence.max_len,
                        approximate=True
                    )
                    
                    # Remove from DLQ
                    await self.persistence._redis.xdel(dlq_key, entry_id)
                    replayed += 1
                    
            except Exception as e:
                logger.error(f"Failed to replay DLQ {dlq_key}: {e}")
                
        logger.info(f"Replayed {replayed} events from DLQ")
        return replayed
        
    async def get_stream_info(self) -> Dict[str, Any]:
        """Get information about the event streams."""
        info = {
            "backend": "redis",
            "streams": {},
            "total_events": 0
        }
        
        # Get info for known event types
        # In production, would use SCAN to find all streams
        for event_type in ["asset", "workflow", "creative"]:
            stream_key = self.persistence._get_stream_key(event_type)
            try:
                stream_info = await self.persistence.get_stream_info(event_type)
                info["streams"][event_type] = stream_info
                info["total_events"] += stream_info.get("length", 0)
            except Exception:
                # Stream might not exist
                pass
                
        return info
        
    async def trim_old_events(
        self,
        max_age_days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Remove events older than specified age."""
        trimmed = 0
        
        if not event_types:
            # Default to known event types
            event_types = ["asset", "workflow", "creative"]
            
        for event_type in event_types:
            try:
                # Get current length before trim
                info = await self.persistence.get_stream_info(event_type)
                before = info.get("length", 0)
                
                # Trim old events
                await self.persistence.trim_old_events(event_type, max_age_days)
                
                # Get length after trim
                info = await self.persistence.get_stream_info(event_type)
                after = info.get("length", 0)
                
                trimmed += max(0, before - after)
            except Exception as e:
                logger.error(f"Failed to trim {event_type}: {e}")
                
        logger.info(f"Trimmed {trimmed} events older than {max_age_days} days")
        return trimmed