"""SQLite implementation of the event store.

This module provides a lightweight, file-based event store using SQLite,
perfect for development and smaller deployments.
"""

import asyncio
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiosqlite

from .base import BaseEvent
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


class SQLiteAcknowledger(EventAcknowledger):
    """SQLite-specific event acknowledger."""
    
    def __init__(
        self,
        store: "SQLiteEventStore",
        event: StoredEvent,
        consumer_group: str,
        consumer_name: str,
        pending_id: int
    ):
        self.store = store
        self.event = event
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.pending_id = pending_id
        self._acknowledged = False
        
    async def ack(self) -> None:
        """Acknowledge successful processing."""
        if self._acknowledged:
            return
            
        try:
            async with self.store._db.execute(
                "DELETE FROM pending_events WHERE id = ?",
                (self.pending_id,)
            ) as cursor:
                await self.store._db.commit()
                
            self._acknowledged = True
            logger.debug(f"Acknowledged event {self.event.event_id}")
        except Exception as e:
            raise AcknowledgmentError(f"Failed to acknowledge: {e}")
    
    async def nack(self, reason: Optional[str] = None) -> None:
        """Negative acknowledgment - update error and increment delivery count."""
        try:
            async with self.store._db.execute(
                """UPDATE pending_events 
                   SET delivery_count = delivery_count + 1,
                       last_error = ?,
                       last_attempt = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (reason, self.pending_id)
            ) as cursor:
                await self.store._db.commit()
                
            if reason:
                logger.warning(f"NACK event {self.event.event_id}: {reason}")
        except Exception as e:
            logger.error(f"Failed to NACK event: {e}")
    
    async def extend_timeout(self, seconds: int) -> None:
        """Extend processing timeout."""
        try:
            new_timeout = datetime.now() + timedelta(seconds=seconds)
            async with self.store._db.execute(
                "UPDATE pending_events SET timeout_at = ? WHERE id = ?",
                (new_timeout.isoformat(), self.pending_id)
            ) as cursor:
                await self.store._db.commit()
        except Exception as e:
            logger.error(f"Failed to extend timeout: {e}")


class SQLiteEventStore(EventStore):
    """SQLite implementation of event store."""
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        max_events: int = 100000,
        pending_timeout_seconds: int = 300
    ):
        """Initialize SQLite event store.
        
        Args:
            db_path: Path to SQLite database file
            max_events: Maximum events to keep (older events are deleted)
            pending_timeout_seconds: Timeout for pending events
        """
        if db_path is None:
            db_path = Path.home() / ".alicemultiverse" / "events.db"
            
        self.db_path = db_path
        self.max_events = max_events
        self.pending_timeout_seconds = pending_timeout_seconds
        self._db: Optional[aiosqlite.Connection] = None
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self) -> None:
        """Establish connection to SQLite."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        
        # Enable WAL mode for better concurrency
        await self._db.execute("PRAGMA journal_mode=WAL")
        
        # Create schema
        await self._create_schema()
        
        logger.info(f"Connected to SQLite event store at {self.db_path}")
        
    async def disconnect(self) -> None:
        """Close connection to SQLite."""
        # Cancel all consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._consumer_tasks:
            await asyncio.gather(
                *self._consumer_tasks.values(),
                return_exceptions=True
            )
            
        if self._db:
            await self._db.close()
            self._db = None
            
    async def _create_schema(self) -> None:
        """Create database schema if not exists."""
        await self._db.executescript("""
            -- Main events table
            CREATE TABLE IF NOT EXISTS events (
                stream_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
            
            -- Consumer groups
            CREATE TABLE IF NOT EXISTS consumer_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Consumer positions (for tracking progress)
            CREATE TABLE IF NOT EXISTS consumer_positions (
                group_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                last_stream_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_name, event_type)
            );
            
            -- Pending events (being processed)
            CREATE TABLE IF NOT EXISTS pending_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id TEXT NOT NULL,
                consumer_group TEXT NOT NULL,
                consumer_name TEXT NOT NULL,
                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timeout_at TIMESTAMP NOT NULL,
                delivery_count INTEGER DEFAULT 1,
                last_error TEXT,
                last_attempt TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES events(stream_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_pending_timeout ON pending_events(timeout_at);
            CREATE INDEX IF NOT EXISTS idx_pending_group ON pending_events(consumer_group);
            
            -- Dead letter queue
            CREATE TABLE IF NOT EXISTS dlq_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_stream_id TEXT NOT NULL,
                event_data TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                failure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_count INTEGER NOT NULL,
                consumer_group TEXT NOT NULL,
                replayed BOOLEAN DEFAULT FALSE
            );
            
            CREATE INDEX IF NOT EXISTS idx_dlq_group ON dlq_events(consumer_group);
            CREATE INDEX IF NOT EXISTS idx_dlq_replayed ON dlq_events(replayed);
        """)
        await self._db.commit()
        
    async def append(self, event: BaseEvent) -> str:
        """Append an event to the store."""
        stream_id = f"{int(datetime.now().timestamp() * 1000000)}-{uuid.uuid4().hex[:8]}"
        event_data = event.to_dict()
        
        await self._db.execute(
            """INSERT INTO events (stream_id, event_id, event_type, event_data, timestamp, source, version)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                stream_id,
                event_data["event_id"],
                event_data["event_type"],
                json.dumps(event_data),
                event_data["timestamp"],
                event_data.get("source"),
                event_data.get("version", 1)
            )
        )
        await self._db.commit()
        
        # Trim old events if needed
        await self._trim_if_needed()
        
        logger.debug(f"Appended event {event.event_id} with stream_id {stream_id}")
        return stream_id
        
    async def get_event(self, stream_id: str) -> Optional[StoredEvent]:
        """Get a single event by its stream ID."""
        async with self._db.execute(
            "SELECT * FROM events WHERE stream_id = ?",
            (stream_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            return None
            
        event_data = json.loads(row["event_data"])
        return StoredEvent(
            event_id=row["event_id"],
            event_type=row["event_type"],
            event_data=event_data,
            timestamp=datetime.fromisoformat(row["timestamp"]),
            stream_id=row["stream_id"]
        )
        
    async def query(self, filter: EventFilter) -> List[StoredEvent]:
        """Query events based on filter criteria."""
        # Build query
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        # Event type filter
        if filter.event_types:
            placeholders = ",".join("?" * len(filter.event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend(filter.event_types)
            
        # Time filters
        if filter.start_time:
            query += " AND timestamp >= ?"
            params.append(filter.start_time.isoformat())
            
        if filter.end_time:
            query += " AND timestamp <= ?"
            params.append(filter.end_time.isoformat())
            
        # ID filters
        if filter.start_id:
            query += " AND stream_id >= ?"
            params.append(filter.start_id)
            
        if filter.end_id:
            query += " AND stream_id <= ?"
            params.append(filter.end_id)
            
        # Source pattern filter
        if filter.source_pattern:
            query += " AND source LIKE ?"
            params.append(f"%{filter.source_pattern}%")
            
        # Order and limit
        query += " ORDER BY stream_id ASC"
        if filter.limit:
            query += " LIMIT ?"
            params.append(filter.limit)
            
        # Execute query
        events = []
        async with self._db.execute(query, params) as cursor:
            async for row in cursor:
                event_data = json.loads(row["event_data"])
                events.append(StoredEvent(
                    event_id=row["event_id"],
                    event_type=row["event_type"],
                    event_data=event_data,
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    stream_id=row["stream_id"]
                ))
                
        return events
        
    async def subscribe(
        self,
        config: ConsumerConfig,
        handler: Callable[[ConsumedEvent], Any]
    ) -> asyncio.Task:
        """Subscribe to events with at-least-once delivery."""
        
        # Ensure consumer group exists
        await self._db.execute(
            "INSERT OR IGNORE INTO consumer_groups (group_name) VALUES (?)",
            (config.consumer_group,)
        )
        await self._db.commit()
        
        async def consumer_loop():
            """Main consumer loop."""
            while True:
                try:
                    # Get events to process
                    events = await self._claim_events(config)
                    
                    if not events:
                        # No events, wait a bit
                        await asyncio.sleep(config.block_timeout_ms / 1000)
                        continue
                        
                    # Process events
                    for pending_id, stored_event, delivery_count, last_error in events:
                        # Create acknowledger
                        ack = SQLiteAcknowledger(
                            self,
                            stored_event,
                            config.consumer_group,
                            config.consumer_name,
                            pending_id
                        )
                        
                        # Create consumed event
                        consumed = ConsumedEvent(
                            event=stored_event,
                            ack=ack,
                            delivery_count=delivery_count,
                            last_error=last_error
                        )
                        
                        # Handle event
                        try:
                            await handler(consumed)
                        except Exception as e:
                            logger.error(f"Handler error for event {stored_event.event_id}: {e}")
                            
                            # Check if should move to DLQ
                            if delivery_count >= config.dead_letter_after:
                                await self.move_to_dlq(consumed, str(e))
                                await ack.ack()  # Remove from pending
                            else:
                                await ack.nack(str(e))
                                
                except asyncio.CancelledError:
                    logger.info(f"Consumer {config.consumer_name} cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Consumer loop error: {e}")
                    await asyncio.sleep(config.retry_delay_ms / 1000)
                    
        # Create and track task
        task = asyncio.create_task(consumer_loop())
        self._consumer_tasks[config.consumer_name] = task
        return task
        
    async def _claim_events(
        self,
        config: ConsumerConfig
    ) -> List[tuple]:
        """Claim events for processing."""
        events = []
        timeout_at = (datetime.now() + timedelta(seconds=self.pending_timeout_seconds)).isoformat()
        
        # Start transaction
        await self._db.execute("BEGIN IMMEDIATE")
        
        try:
            # Get last positions for this consumer group
            positions = {}
            async with self._db.execute(
                "SELECT event_type, last_stream_id FROM consumer_positions WHERE group_name = ?",
                (config.consumer_group,)
            ) as cursor:
                async for row in cursor:
                    positions[row["event_type"]] = row["last_stream_id"]
                    
            # Claim events for each event type
            for event_type in config.event_types:
                last_id = positions.get(event_type, "")
                
                # Get unclaimed events
                query = """
                    SELECT e.* FROM events e
                    LEFT JOIN pending_events p ON e.stream_id = p.stream_id 
                        AND p.consumer_group = ?
                    WHERE e.event_type = ? 
                        AND e.stream_id > ?
                        AND p.id IS NULL
                    ORDER BY e.stream_id
                    LIMIT ?
                """
                
                async with self._db.execute(
                    query,
                    (config.consumer_group, event_type, last_id, config.batch_size)
                ) as cursor:
                    async for row in cursor:
                        # Add to pending
                        async with self._db.execute(
                            """INSERT INTO pending_events 
                               (stream_id, consumer_group, consumer_name, timeout_at)
                               VALUES (?, ?, ?, ?)""",
                            (row["stream_id"], config.consumer_group, config.consumer_name, timeout_at)
                        ) as insert_cursor:
                            pending_id = insert_cursor.lastrowid
                            
                        # Create stored event
                        event_data = json.loads(row["event_data"])
                        stored_event = StoredEvent(
                            event_id=row["event_id"],
                            event_type=row["event_type"],
                            event_data=event_data,
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            stream_id=row["stream_id"]
                        )
                        
                        events.append((pending_id, stored_event, 1, None))
                        
                        # Update position
                        await self._db.execute(
                            """INSERT OR REPLACE INTO consumer_positions 
                               (group_name, event_type, last_stream_id, updated_at)
                               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                            (config.consumer_group, event_type, row["stream_id"])
                        )
                        
            # Also check for timed-out pending events
            async with self._db.execute(
                """SELECT p.*, e.* FROM pending_events p
                   JOIN events e ON p.stream_id = e.stream_id
                   WHERE p.consumer_group = ?
                     AND p.timeout_at < CURRENT_TIMESTAMP
                   LIMIT ?""",
                (config.consumer_group, config.batch_size - len(events))
            ) as cursor:
                async for row in cursor:
                    # Re-claim with new timeout
                    await self._db.execute(
                        """UPDATE pending_events 
                           SET consumer_name = ?, timeout_at = ?, claimed_at = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (config.consumer_name, timeout_at, row["id"])
                    )
                    
                    # Create stored event
                    event_data = json.loads(row["event_data"])
                    stored_event = StoredEvent(
                        event_id=row["event_id"],
                        event_type=row["event_type"],
                        event_data=event_data,
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        stream_id=row["stream_id"]
                    )
                    
                    events.append((
                        row["id"],
                        stored_event,
                        row["delivery_count"],
                        row["last_error"]
                    ))
                    
            await self._db.commit()
            
        except Exception as e:
            await self._db.rollback()
            raise EventStoreError(f"Failed to claim events: {e}")
            
        return events
        
    async def get_pending_events(
        self,
        consumer_group: str,
        max_idle_ms: int = 60000
    ) -> List[ConsumedEvent]:
        """Get events that have been pending for too long."""
        events = []
        cutoff = datetime.now() - timedelta(milliseconds=max_idle_ms)
        
        async with self._db.execute(
            """SELECT p.*, e.* FROM pending_events p
               JOIN events e ON p.stream_id = e.stream_id
               WHERE p.consumer_group = ?
                 AND p.claimed_at < ?""",
            (consumer_group, cutoff.isoformat())
        ) as cursor:
            async for row in cursor:
                # Create stored event
                event_data = json.loads(row["event_data"])
                stored_event = StoredEvent(
                    event_id=row["event_id"],
                    event_type=row["event_type"],
                    event_data=event_data,
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    stream_id=row["stream_id"]
                )
                
                # Create acknowledger
                ack = SQLiteAcknowledger(
                    self,
                    stored_event,
                    consumer_group,
                    row["consumer_name"],
                    row["id"]
                )
                
                events.append(ConsumedEvent(
                    event=stored_event,
                    ack=ack,
                    delivery_count=row["delivery_count"],
                    last_error=row["last_error"]
                ))
                
        return events
        
    async def move_to_dlq(
        self,
        event: ConsumedEvent,
        reason: str
    ) -> None:
        """Move an event to the dead letter queue."""
        await self._db.execute(
            """INSERT INTO dlq_events 
               (original_stream_id, event_data, failure_reason, delivery_count, consumer_group)
               VALUES (?, ?, ?, ?, ?)""",
            (
                event.event.stream_id,
                json.dumps(event.event.event_data),
                reason,
                event.delivery_count,
                "unknown"  # Would need to pass consumer group
            )
        )
        await self._db.commit()
        
        logger.info(f"Moved event {event.event.event_id} to DLQ: {reason}")
        
    async def replay_dlq(
        self,
        consumer_group: str,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Replay events from dead letter queue."""
        replayed = 0
        
        # Build query
        query = """SELECT * FROM dlq_events 
                   WHERE consumer_group = ? AND replayed = FALSE"""
        params = [consumer_group]
        
        if event_types:
            # Need to parse event_data to filter by type
            # For simplicity, replay all for now
            pass
            
        async with self._db.execute(query, params) as cursor:
            async for row in cursor:
                # Re-insert into events table
                event_data = json.loads(row["event_data"])
                stream_id = await self.append(BaseEvent(**event_data))
                
                # Mark as replayed
                await self._db.execute(
                    "UPDATE dlq_events SET replayed = TRUE WHERE id = ?",
                    (row["id"],)
                )
                
                replayed += 1
                
        await self._db.commit()
        logger.info(f"Replayed {replayed} events from DLQ")
        return replayed
        
    async def get_stream_info(self) -> Dict[str, Any]:
        """Get information about the event streams."""
        info = {
            "backend": "sqlite",
            "database": str(self.db_path),
            "events": {},
            "total_events": 0,
            "pending_events": 0,
            "dlq_events": 0
        }
        
        # Count events by type
        async with self._db.execute(
            "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type"
        ) as cursor:
            async for row in cursor:
                info["events"][row["event_type"]] = row["count"]
                info["total_events"] += row["count"]
                
        # Count pending events
        async with self._db.execute(
            "SELECT COUNT(*) as count FROM pending_events"
        ) as cursor:
            row = await cursor.fetchone()
            info["pending_events"] = row["count"]
            
        # Count DLQ events
        async with self._db.execute(
            "SELECT COUNT(*) as count FROM dlq_events WHERE replayed = FALSE"
        ) as cursor:
            row = await cursor.fetchone()
            info["dlq_events"] = row["count"]
            
        return info
        
    async def trim_old_events(
        self,
        max_age_days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Remove events older than specified age."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        # Build query
        query = "DELETE FROM events WHERE timestamp < ?"
        params = [cutoff.isoformat()]
        
        if event_types:
            placeholders = ",".join("?" * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
            
        cursor = await self._db.execute(query, params)
        deleted = cursor.rowcount
        await self._db.commit()
        
        logger.info(f"Trimmed {deleted} events older than {max_age_days} days")
        return deleted
        
    async def _trim_if_needed(self) -> None:
        """Trim events if over limit."""
        async with self._db.execute("SELECT COUNT(*) FROM events") as cursor:
            row = await cursor.fetchone()
            count = row[0]
            
        if count > self.max_events:
            # Delete oldest events
            to_delete = count - self.max_events
            await self._db.execute(
                "DELETE FROM events WHERE stream_id IN (SELECT stream_id FROM events ORDER BY stream_id LIMIT ?)",
                (to_delete,)
            )
            await self._db.commit()
            logger.debug(f"Trimmed {to_delete} old events")