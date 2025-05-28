"""PostgreSQL-native event system using NOTIFY/LISTEN.

Simple, direct event publishing and subscription without unnecessary abstractions.
Uses PostgreSQL's built-in pub/sub for real-time events and a table for persistence.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from alicemultiverse.database.config import DATABASE_URL, get_session

logger = logging.getLogger(__name__)


class PostgresEventSystem:
    """Simple PostgreSQL-based event system."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the event system.
        
        Args:
            database_url: PostgreSQL connection URL. Uses DATABASE_URL env var if not provided.
        """
        self.database_url = database_url or DATABASE_URL
        self._listeners: Dict[str, List[Callable]] = {}
        self._listen_task: Optional[asyncio.Task] = None
        self._connection: Optional[asyncpg.Connection] = None
        
    def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event synchronously.
        
        Args:
            event_type: Type of event (e.g., "asset.processed")
            data: Event data
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        event_data = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in database
        with get_session() as session:
            session.execute(
                text("""
                    INSERT INTO events (id, type, data, created_at)
                    VALUES (:id, :type, :data, :created_at)
                """),
                {
                    "id": event_id,
                    "type": event_type,
                    "data": json.dumps(event_data),
                    "created_at": datetime.now(timezone.utc)
                }
            )
            session.commit()
            
            # Notify listeners
            session.execute(
                text("SELECT pg_notify(:channel, :payload)"),
                {
                    "channel": "events",
                    "payload": json.dumps({"id": event_id, "type": event_type})
                }
            )
            session.commit()
            
        logger.debug(f"Published event {event_type} with ID {event_id}")
        return event_id
    
    async def publish_async(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event asynchronously.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        event_data = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Connect if needed
        if not self._connection:
            self._connection = await asyncpg.connect(self.database_url)
        
        # Store and notify in a transaction
        async with self._connection.transaction():
            await self._connection.execute(
                """
                INSERT INTO events (id, type, data, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                event_id,
                event_type,
                json.dumps(event_data),
                datetime.now(timezone.utc)
            )
            
            await self._connection.execute(
                "SELECT pg_notify($1, $2)",
                "events",
                json.dumps({"id": event_id, "type": event_type})
            )
        
        logger.debug(f"Published event {event_type} with ID {event_id}")
        return event_id
    
    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to events of a specific type.
        
        Args:
            event_type: Event type to subscribe to (supports wildcards like "asset.*")
            handler: Function to call when event is received
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from events.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._listeners:
            self._listeners[event_type].remove(handler)
            if not self._listeners[event_type]:
                del self._listeners[event_type]
    
    async def start_listening(self) -> None:
        """Start listening for events. Call this once in your async app."""
        if self._listen_task:
            return
            
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Started PostgreSQL event listener")
    
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
            
        if self._connection:
            await self._connection.close()
            self._connection = None
            
        logger.info("Stopped PostgreSQL event listener")
    
    async def _listen_loop(self) -> None:
        """Internal loop for listening to PostgreSQL notifications."""
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.add_listener("events", self._handle_notification)
            
            # Keep connection alive
            while True:
                await asyncio.sleep(60)  # Heartbeat
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in event listener: {e}")
        finally:
            await conn.remove_listener("events", self._handle_notification)
            await conn.close()
    
    def _handle_notification(self, connection, pid, channel, payload):
        """Handle PostgreSQL notification."""
        try:
            notification = json.loads(payload)
            event_id = notification["id"]
            event_type = notification["type"]
            
            # Fetch full event data
            asyncio.create_task(self._process_event(event_id, event_type))
            
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    async def _process_event(self, event_id: str, event_type: str) -> None:
        """Process an event by fetching data and calling handlers."""
        try:
            # Fetch event data
            if not self._connection:
                self._connection = await asyncpg.connect(self.database_url)
                
            row = await self._connection.fetchrow(
                "SELECT data FROM events WHERE id = $1",
                event_id
            )
            
            if not row:
                logger.error(f"Event {event_id} not found")
                return
                
            event_data = json.loads(row["data"])
            
            # Call matching handlers
            for pattern, handlers in self._listeners.items():
                if self._matches_pattern(event_type, pattern):
                    for handler in handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event_data)
                            else:
                                handler(event_data)
                        except Exception as e:
                            logger.error(f"Error in event handler: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
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
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent events from the database.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            
        Returns:
            List of events
        """
        with get_session() as session:
            query = text("""
                SELECT data 
                FROM events 
                WHERE (:event_type IS NULL OR type = :event_type)
                ORDER BY created_at DESC 
                LIMIT :limit
            """)
            
            result = session.execute(
                query,
                {"event_type": event_type, "limit": limit}
            )
            
            # PostgreSQL automatically parses JSON columns
            return [row[0] for row in result]


# Global instance for convenience
_event_system: Optional[PostgresEventSystem] = None


def get_event_system() -> PostgresEventSystem:
    """Get the global event system instance."""
    global _event_system
    if _event_system is None:
        _event_system = PostgresEventSystem()
    return _event_system


# Convenience functions for simple usage
def publish_event(event_type: str, data: Dict[str, Any]) -> str:
    """Publish an event using the global event system."""
    return get_event_system().publish(event_type, data)


def subscribe_to_events(event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """Subscribe to events using the global event system."""
    get_event_system().subscribe(event_type, handler)