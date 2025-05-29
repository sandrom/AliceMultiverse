"""Event persistence layer using Redis Streams.

This module provides reliable event storage and retrieval using Redis Streams,
enabling event sourcing, replay, and guaranteed delivery.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import asdict

try:
    import redis.asyncio as redis
    from redis.asyncio.client import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

from .base_v2 import BaseEvent

logger = logging.getLogger(__name__)


class EventPersistence:
    """Handles event persistence using Redis Streams."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 stream_prefix: str = "alice:events:",
                 consumer_group: str = "alice-main",
                 max_len: int = 100000):
        """Initialize event persistence.
        
        Args:
            redis_url: Redis connection URL
            stream_prefix: Prefix for stream keys
            consumer_group: Default consumer group name
            max_len: Maximum events per stream (FIFO eviction)
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not installed. Install with: pip install redis>=5.0.0"
            )
        
        self.redis_url = redis_url
        self.stream_prefix = stream_prefix
        self.consumer_group = consumer_group
        self.max_len = max_len
        self._redis: Optional[Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        if not self._redis:
            self._redis = await redis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"Connected to Redis at {self.redis_url}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    def _get_stream_key(self, event_type: str) -> str:
        """Get Redis stream key for event type."""
        return f"{self.stream_prefix}{event_type}"
    
    def _get_global_stream_key(self) -> str:
        """Get Redis stream key for all events."""
        return f"{self.stream_prefix}all"
    
    async def persist_event(self, event: BaseEvent) -> str:
        """Persist an event to Redis Streams.
        
        Args:
            event: Event to persist
            
        Returns:
            Redis stream entry ID
        """
        if not self._redis:
            await self.connect()
        
        # Serialize event
        event_data = event.to_dict()
        event_json = json.dumps(event_data, default=str)
        
        # Store in type-specific stream
        stream_key = self._get_stream_key(event.event_type)
        entry_id = await self._redis.xadd(
            stream_key,
            {"event": event_json},
            maxlen=self.max_len,
            approximate=True
        )
        
        # Also store in global stream for monitoring
        await self._redis.xadd(
            self._get_global_stream_key(),
            {
                "event": event_json,
                "type": event.event_type
            },
            maxlen=self.max_len * 2,  # Keep more in global stream
            approximate=True
        )
        
        logger.debug(f"Persisted {event.event_type} event {event.event_id} to stream {entry_id}")
        return entry_id
    
    async def get_events(self, event_type: str, 
                        start: str = "-", 
                        end: str = "+",
                        count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get events from a stream.
        
        Args:
            event_type: Type of events to retrieve
            start: Start ID or timestamp (- for beginning)
            end: End ID or timestamp (+ for end)
            count: Maximum number of events to return
            
        Returns:
            List of events with metadata
        """
        if not self._redis:
            await self.connect()
        
        stream_key = self._get_stream_key(event_type)
        
        # Get events from stream
        if count:
            entries = await self._redis.xrange(stream_key, min=start, max=end, count=count)
        else:
            entries = await self._redis.xrange(stream_key, min=start, max=end)
        
        events = []
        for entry_id, data in entries:
            event_data = json.loads(data["event"])
            events.append({
                "stream_id": entry_id,
                "event": event_data
            })
        
        return events
    
    async def consume_events(self, event_types: List[str],
                           consumer_name: str,
                           block_ms: int = 1000,
                           count: int = 10) -> AsyncIterator[Dict[str, Any]]:
        """Consume events from streams using consumer groups.
        
        Args:
            event_types: List of event types to consume
            consumer_name: Name of this consumer
            block_ms: Milliseconds to block waiting for events
            count: Maximum events to read per iteration
            
        Yields:
            Event data with acknowledgment callback
        """
        if not self._redis:
            await self.connect()
        
        # Create consumer groups if they don't exist
        streams = {}
        for event_type in event_types:
            stream_key = self._get_stream_key(event_type)
            streams[stream_key] = ">"  # Read new messages
            
            try:
                await self._redis.xgroup_create(
                    stream_key, 
                    self.consumer_group,
                    id="0",
                    mkstream=True
                )
                logger.info(f"Created consumer group {self.consumer_group} for {stream_key}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
        
        # Consume events
        while True:
            try:
                # Read from multiple streams
                messages = await self._redis.xreadgroup(
                    self.consumer_group,
                    consumer_name,
                    streams,
                    count=count,
                    block=block_ms
                )
                
                for stream_key, stream_messages in messages:
                    for msg_id, data in stream_messages:
                        event_data = json.loads(data["event"])
                        
                        # Create acknowledgment callback
                        async def ack():
                            await self._redis.xack(stream_key, self.consumer_group, msg_id)
                            logger.debug(f"Acknowledged message {msg_id} from {stream_key}")
                        
                        yield {
                            "stream_key": stream_key,
                            "message_id": msg_id,
                            "event": event_data,
                            "ack": ack
                        }
            
            except Exception as e:
                logger.error(f"Error consuming events: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def get_pending_events(self, event_type: str,
                               consumer_name: Optional[str] = None,
                               idle_ms: int = 60000) -> List[Dict[str, Any]]:
        """Get pending (unacknowledged) events.
        
        Args:
            event_type: Type of events to check
            consumer_name: Specific consumer to check (None for all)
            idle_ms: Minimum idle time in milliseconds
            
        Returns:
            List of pending events
        """
        if not self._redis:
            await self.connect()
        
        stream_key = self._get_stream_key(event_type)
        
        # Get pending entries
        pending = await self._redis.xpending_range(
            stream_key,
            self.consumer_group,
            min="-",
            max="+",
            count=100,
            consumername=consumer_name
        )
        
        events = []
        for entry in pending:
            if entry["idle"] >= idle_ms:
                # Claim and return the message
                claimed = await self._redis.xclaim(
                    stream_key,
                    self.consumer_group,
                    consumer_name or "reclaimer",
                    min_idle_time=idle_ms,
                    message_ids=[entry["message_id"]]
                )
                
                if claimed:
                    msg_id, data = claimed[0]
                    event_data = json.loads(data["event"])
                    events.append({
                        "stream_id": msg_id,
                        "event": event_data,
                        "idle_ms": entry["idle"],
                        "delivery_count": entry["times_delivered"]
                    })
        
        return events
    
    async def trim_old_events(self, event_type: str, max_age_days: int = 30):
        """Trim events older than specified age.
        
        Args:
            event_type: Type of events to trim
            max_age_days: Maximum age in days
        """
        if not self._redis:
            await self.connect()
        
        stream_key = self._get_stream_key(event_type)
        
        # Calculate cutoff timestamp
        cutoff = datetime.now() - timedelta(days=max_age_days)
        cutoff_ms = int(cutoff.timestamp() * 1000)
        
        # Trim stream
        await self._redis.xtrim(
            stream_key,
            minid=f"{cutoff_ms}-0",
            approximate=False
        )
        
        logger.info(f"Trimmed events older than {max_age_days} days from {stream_key}")
    
    async def get_stream_info(self, event_type: str) -> Dict[str, Any]:
        """Get information about an event stream.
        
        Args:
            event_type: Type of events
            
        Returns:
            Stream information including length, first/last entry
        """
        if not self._redis:
            await self.connect()
        
        stream_key = self._get_stream_key(event_type)
        
        # Get stream info
        info = await self._redis.xinfo_stream(stream_key)
        
        # Get consumer group info if exists
        try:
            groups = await self._redis.xinfo_groups(stream_key)
            info["consumer_groups"] = groups
        except:
            info["consumer_groups"] = []
        
        return info


# Global persistence instance
_persistence: Optional[EventPersistence] = None


async def get_persistence(redis_url: Optional[str] = None) -> EventPersistence:
    """Get or create global persistence instance."""
    global _persistence
    
    if not _persistence:
        url = redis_url or "redis://localhost:6379"
        _persistence = EventPersistence(redis_url=url)
        await _persistence.connect()
    
    return _persistence


import asyncio  # Add this import at the top if not already present