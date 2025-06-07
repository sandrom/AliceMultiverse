"""Redis Streams event system.

High-performance event streaming using Redis Streams with consumer groups.
Provides reliable, persistent event delivery with automatic retries.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import redis.asyncio as redis
from redis.exceptions import ResponseError

from alicemultiverse.core.config import settings
from alicemultiverse.core.structured_logging import get_logger
from alicemultiverse.core.metrics import events_published_total, event_processing_duration_seconds

logger = get_logger(__name__)


class RedisStreamsEventSystem:
    """Redis Streams-based event system with consumer groups."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize the event system.
        
        Args:
            redis_url: Redis connection URL. Uses REDIS_URL env var if not provided.
        """
        self.redis_url = redis_url or settings.get("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None
        self._listeners: Dict[str, List[Callable]] = {}
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        self._running: bool = False
        self._consumer_group = f"alice-{uuid.uuid4().hex[:8]}"  # Unique group per instance
        
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if not self._redis:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        return self._redis
        
    async def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event asynchronously.
        
        Args:
            event_type: Type of event (e.g., "asset.processed")
            data: Event data
            
        Returns:
            Event ID (Redis stream entry ID)
        """
        event_id = str(uuid.uuid4())
        
        # Track metrics
        events_published_total.labels(event_type=event_type).inc()
        
        event_data = {
            "id": event_id,
            "type": event_type,
            "data": json.dumps(data),  # JSON encode nested data
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            client = await self._get_redis()
            
            # Add to stream
            stream_key = f"events:{event_type}"
            stream_id = await client.xadd(
                stream_key,
                event_data,
                maxlen=10000  # Keep last 10k events per type
            )
            
            # Also add to global stream for monitoring
            await client.xadd(
                "events:all",
                {
                    **event_data,
                    "stream": stream_key,
                    "stream_id": stream_id
                },
                maxlen=50000  # Keep last 50k events total
            )
            
            logger.debug(f"Published event {event_type} with ID {event_id} (stream ID: {stream_id})")
            return stream_id
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise
    
    def publish_sync(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event synchronously.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Event ID
        """
        # Run async publish in new event loop
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.publish(event_type, data))
        finally:
            loop.close()
    
    async def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Event type to subscribe to (supports wildcards like "asset.*")
            handler: Function to call when event is received
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
        
        # Start consumer if we're running
        if self._running and event_type not in self._consumer_tasks:
            await self._start_consumer(event_type)
            
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
                
                # Stop consumer if no more listeners
                if event_type in self._consumer_tasks:
                    self._consumer_tasks[event_type].cancel()
                    del self._consumer_tasks[event_type]
    
    async def start_listening(self) -> None:
        """Start listening for events. Call this once in your async app."""
        if self._running:
            return
            
        self._running = True
        await self._get_redis()
        
        # Create consumer group for each subscribed event type
        for event_type in self._listeners:
            await self._start_consumer(event_type)
            
        logger.info(f"Started Redis Streams event listener (group: {self._consumer_group})")
    
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        self._running = False
        
        # Cancel all consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
            
        # Wait for tasks to complete
        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks.values(), return_exceptions=True)
        self._consumer_tasks.clear()
        
        # Close Redis connection
        if self._redis:
            await self._redis.close()
            self._redis = None
            
        logger.info("Stopped Redis Streams event listener")
    
    async def _start_consumer(self, event_type: str) -> None:
        """Start a consumer task for a specific event type."""
        stream_key = f"events:{event_type}"
        client = await self._get_redis()
        
        # Create consumer group (ignore error if already exists)
        try:
            await client.xgroup_create(stream_key, self._consumer_group, id="0")
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
                
        # Start consumer task
        task = asyncio.create_task(self._consume_stream(event_type))
        self._consumer_tasks[event_type] = task
    
    async def _consume_stream(self, event_type: str) -> None:
        """Consume events from a Redis stream."""
        stream_key = f"events:{event_type}"
        client = await self._get_redis()
        consumer_name = f"{self._consumer_group}-{event_type}"
        
        try:
            while self._running:
                try:
                    # Read from stream with consumer group
                    messages = await client.xreadgroup(
                        self._consumer_group,
                        consumer_name,
                        {stream_key: ">"},  # Read only new messages
                        count=10,
                        block=1000  # Block for 1 second
                    )
                    
                    if not messages:
                        continue
                        
                    # Process messages
                    for stream, stream_messages in messages:
                        for msg_id, data in stream_messages:
                            await self._process_message(event_type, msg_id, data)
                            
                            # Acknowledge message
                            await client.xack(stream_key, self._consumer_group, msg_id)
                            
                except Exception as e:
                    logger.error(f"Error consuming stream {stream_key}: {e}")
                    await asyncio.sleep(1)  # Back off on error
                    
        except asyncio.CancelledError:
            logger.debug(f"Consumer for {event_type} cancelled")
            raise
    
    async def _process_message(self, event_type: str, msg_id: str, data: Dict[str, Any]) -> None:
        """Process a message from the stream."""
        try:
            # Parse JSON data field
            if "data" in data and isinstance(data["data"], str):
                data["data"] = json.loads(data["data"])
                
            # Track processing time
            start_time = time.time()
            
            # Call handlers for exact match
            if event_type in self._listeners:
                for handler in self._listeners[event_type]:
                    await self._call_handler(handler, data)
                    
            # Call handlers for wildcard patterns
            for pattern, handlers in self._listeners.items():
                if pattern != event_type and self._matches_pattern(event_type, pattern):
                    for handler in handlers:
                        await self._call_handler(handler, data)
                        
            # Record metrics
            duration = time.time() - start_time
            event_processing_duration_seconds.labels(event_type=event_type).observe(duration)
            
        except Exception as e:
            logger.error(f"Error processing message {msg_id}: {e}")
    
    async def _call_handler(self, handler: Callable, data: Dict[str, Any]) -> None:
        """Call an event handler safely."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(data)
            else:
                # Run sync handler in thread pool
                await asyncio.get_running_loop().run_in_executor(None, handler, data)
        except Exception as e:
            logger.error(f"Error in event handler: {e}")
    
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
        """Get recent events from Redis streams.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            start_time: Start time for range query (Redis stream ID format)
            end_time: End time for range query (Redis stream ID format)
            
        Returns:
            List of events
        """
        client = await self._get_redis()
        events = []
        
        try:
            if event_type:
                # Get from specific stream
                stream_key = f"events:{event_type}"
                start = start_time or "-"
                end = end_time or "+"
                
                messages = await client.xrange(stream_key, start, end, count=limit)
                
                for msg_id, data in messages:
                    if "data" in data and isinstance(data["data"], str):
                        data["data"] = json.loads(data["data"])
                    events.append({
                        "stream_id": msg_id,
                        **data
                    })
            else:
                # Get from global stream
                start = start_time or "-"
                end = end_time or "+"
                
                messages = await client.xrevrange("events:all", end, start, count=limit)
                
                for msg_id, data in messages:
                    if "data" in data and isinstance(data["data"], str):
                        data["data"] = json.loads(data["data"])
                    events.append({
                        "stream_id": msg_id,
                        **data
                    })
                    
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            
        return events
    
    async def get_pending_messages(self, event_type: str) -> List[Dict[str, Any]]:
        """Get pending (unacknowledged) messages for this consumer group.
        
        Args:
            event_type: Event type to check
            
        Returns:
            List of pending messages
        """
        client = await self._get_redis()
        stream_key = f"events:{event_type}"
        
        try:
            # Get pending messages for the consumer group
            pending = await client.xpending(stream_key, self._consumer_group)
            
            if not pending or pending[0] == 0:
                return []
                
            # Get detailed info about pending messages
            messages = await client.xpending_range(
                stream_key,
                self._consumer_group,
                min="-",
                max="+",
                count=100
            )
            
            return [
                {
                    "message_id": msg[0],
                    "consumer": msg[1],
                    "idle_time_ms": msg[2],
                    "delivery_count": msg[3]
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending messages: {e}")
            return []
    
    async def claim_abandoned_messages(self, event_type: str, idle_time_ms: int = 60000) -> int:
        """Claim messages that have been idle for too long.
        
        Args:
            event_type: Event type to check
            idle_time_ms: Consider messages idle after this many milliseconds
            
        Returns:
            Number of messages claimed
        """
        client = await self._get_redis()
        stream_key = f"events:{event_type}"
        consumer_name = f"{self._consumer_group}-{event_type}"
        
        try:
            # Get pending messages
            pending = await self.get_pending_messages(event_type)
            
            claimed = 0
            for msg in pending:
                if msg["idle_time_ms"] > idle_time_ms:
                    # Claim the message
                    result = await client.xclaim(
                        stream_key,
                        self._consumer_group,
                        consumer_name,
                        min_idle_time=idle_time_ms,
                        message_ids=[msg["message_id"]]
                    )
                    
                    if result:
                        claimed += 1
                        logger.info(f"Claimed abandoned message {msg['message_id']}")
                        
            return claimed
            
        except Exception as e:
            logger.error(f"Error claiming abandoned messages: {e}")
            return 0


# Global instance for convenience
_event_system: Optional[RedisStreamsEventSystem] = None


def get_event_system() -> RedisStreamsEventSystem:
    """Get the global event system instance."""
    global _event_system
    if _event_system is None:
        _event_system = RedisStreamsEventSystem()
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