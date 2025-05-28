"""PostgreSQL-based event store using NOTIFY/LISTEN.

This implementation uses PostgreSQL's built-in pub/sub mechanism for real-time
event distribution and a table for persistence.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

import asyncpg
from sqlalchemy import text

from alicemultiverse.database.config import DATABASE_URL

from .base import BaseEvent
from .store import ConsumerConfig, EventFilter, EventStore, StoredEvent

logger = logging.getLogger(__name__)


class PostgresEventStore(EventStore):
    """PostgreSQL implementation of event store using NOTIFY/LISTEN."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize PostgreSQL event store.
        
        Args:
            database_url: PostgreSQL connection URL. Uses DATABASE_URL env var if not provided.
        """
        self.database_url = database_url or DATABASE_URL
        self._listeners: Dict[str, List[asyncio.Queue]] = {}
        self._connection_pool: Optional[asyncpg.Pool] = None
        self._listener_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize the event store and create tables if needed."""
        # Create connection pool
        self._connection_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        
        # Create events table if it doesn't exist
        async with self._connection_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    event_type VARCHAR(255) NOT NULL,
                    event_data JSONB NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    source VARCHAR(255),
                    version VARCHAR(50),
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
                CREATE INDEX IF NOT EXISTS idx_events_data_gin ON events USING GIN(event_data);
            """)
            
            # Create consumer groups table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS event_consumer_groups (
                    group_name VARCHAR(255) NOT NULL,
                    consumer_name VARCHAR(255) NOT NULL,
                    last_event_id INTEGER,
                    last_processed_at TIMESTAMPTZ,
                    PRIMARY KEY (group_name, consumer_name)
                );
            """)
        
        # Start listener for NOTIFY/LISTEN
        self._listener_task = asyncio.create_task(self._listen_for_events())
        logger.info("PostgreSQL event store initialized")
    
    async def _listen_for_events(self) -> None:
        """Listen for PostgreSQL NOTIFY events."""
        conn = await asyncpg.connect(self.database_url)
        try:
            # Listen on the events channel
            await conn.add_listener('events', self._handle_notification)
            
            # Keep connection alive
            while True:
                await asyncio.sleep(60)  # Heartbeat
                await conn.fetchval("SELECT 1")
        except Exception as e:
            logger.error(f"Listener error: {e}")
        finally:
            await conn.close()
    
    def _handle_notification(self, connection, pid, channel, payload):
        """Handle PostgreSQL NOTIFY notification."""
        try:
            data = json.loads(payload)
            event_type = data.get('event_type')
            
            # Deliver to subscribers
            if event_type in self._listeners:
                for queue in self._listeners[event_type]:
                    # Non-blocking put
                    try:
                        queue.put_nowait(data)
                    except asyncio.QueueFull:
                        logger.warning(f"Queue full for event type {event_type}")
            
            # Also deliver to wildcard subscribers
            if '*' in self._listeners:
                for queue in self._listeners['*']:
                    try:
                        queue.put_nowait(data)
                    except asyncio.QueueFull:
                        logger.warning("Queue full for wildcard subscriber")
                        
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    async def store_event(self, event: BaseEvent) -> str:
        """Store an event and notify listeners.
        
        Args:
            event: Event to store
            
        Returns:
            Stream ID of the stored event
        """
        async with self._connection_pool.acquire() as conn:
            # Store event in table
            row = await conn.fetchrow("""
                INSERT INTO events (
                    event_id, event_type, event_data, 
                    timestamp, source, version, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
                event.event_id,
                event.event_type,
                json.dumps(event.to_dict()),
                event.timestamp,
                event.source,
                event.version,
                json.dumps(getattr(event, 'metadata', {}))
            )
            
            stream_id = str(row['id'])
            
            # Notify listeners
            notification_data = {
                'stream_id': stream_id,
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat()
            }
            
            await conn.execute(
                "SELECT pg_notify('events', $1)",
                json.dumps(notification_data)
            )
            
            return stream_id
    
    async def get_events(
        self,
        filter: Optional[EventFilter] = None,
        consumer_config: Optional[ConsumerConfig] = None
    ) -> AsyncIterator[StoredEvent]:
        """Get events matching the filter criteria.
        
        Args:
            filter: Filter criteria
            consumer_config: Consumer configuration for tracking progress
            
        Yields:
            Stored events matching criteria
        """
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        param_count = 0
        
        if filter:
            if filter.event_types:
                param_count += 1
                query += f" AND event_type = ANY(${param_count})"
                params.append(filter.event_types)
            
            if filter.start_time:
                param_count += 1
                query += f" AND timestamp >= ${param_count}"
                params.append(filter.start_time)
            
            if filter.end_time:
                param_count += 1
                query += f" AND timestamp <= ${param_count}"
                params.append(filter.end_time)
            
            if filter.start_id:
                param_count += 1
                query += f" AND id > ${param_count}"
                params.append(int(filter.start_id))
        
        # Handle consumer group tracking
        if consumer_config:
            last_id = await self._get_consumer_position(
                consumer_config.consumer_group,
                consumer_config.consumer_name
            )
            if last_id:
                param_count += 1
                query += f" AND id > ${param_count}"
                params.append(last_id)
        
        query += " ORDER BY id ASC"
        
        if filter and filter.limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(filter.limit)
        
        async with self._connection_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            for row in rows:
                event = StoredEvent(
                    event_id=row['event_id'],
                    event_type=row['event_type'],
                    event_data=row['event_data'],
                    timestamp=row['timestamp'],
                    stream_id=str(row['id']),
                    metadata=row['metadata']
                )
                
                # Update consumer position
                if consumer_config:
                    await self._update_consumer_position(
                        consumer_config.consumer_group,
                        consumer_config.consumer_name,
                        row['id']
                    )
                
                yield event
    
    async def subscribe_to_events(
        self,
        event_types: List[str],
        start_from: Optional[str] = None
    ) -> AsyncIterator[StoredEvent]:
        """Subscribe to real-time events.
        
        Args:
            event_types: Event types to subscribe to (use ['*'] for all)
            start_from: Stream ID to start from (default: latest)
            
        Yields:
            Events as they occur
        """
        # Create queue for this subscriber
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        # Register queue for each event type
        for event_type in event_types:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(queue)
        
        try:
            # First, catch up on any missed events
            if start_from:
                filter = EventFilter(
                    event_types=event_types if '*' not in event_types else None,
                    start_id=start_from
                )
                async for event in self.get_events(filter):
                    yield event
            
            # Then listen for new events
            while True:
                notification = await queue.get()
                
                # Fetch the full event
                async with self._connection_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM events WHERE id = $1",
                        int(notification['stream_id'])
                    )
                    
                    if row:
                        yield StoredEvent(
                            event_id=row['event_id'],
                            event_type=row['event_type'],
                            event_data=row['event_data'],
                            timestamp=row['timestamp'],
                            stream_id=str(row['id']),
                            metadata=row['metadata']
                        )
        finally:
            # Cleanup
            for event_type in event_types:
                if event_type in self._listeners:
                    self._listeners[event_type].remove(queue)
    
    async def _get_consumer_position(self, group: str, consumer: str) -> Optional[int]:
        """Get last processed event ID for a consumer."""
        async with self._connection_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_event_id FROM event_consumer_groups WHERE group_name = $1 AND consumer_name = $2",
                group, consumer
            )
            return row['last_event_id'] if row else None
    
    async def _update_consumer_position(self, group: str, consumer: str, event_id: int) -> None:
        """Update consumer position."""
        async with self._connection_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO event_consumer_groups (group_name, consumer_name, last_event_id, last_processed_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (group_name, consumer_name)
                DO UPDATE SET last_event_id = $3, last_processed_at = $4
            """, group, consumer, event_id, datetime.now(timezone.utc))
    
    async def close(self) -> None:
        """Close connections and cleanup."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self._connection_pool:
            await self._connection_pool.close()
        
        logger.info("PostgreSQL event store closed")