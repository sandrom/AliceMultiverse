"""In-memory implementation of the event store for testing.

This module provides a simple in-memory event store that's perfect
for unit tests and development.
"""

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from .base import BaseEvent
from .store import (
    AcknowledgmentError,
    ConsumedEvent,
    ConsumerConfig,
    EventAcknowledger,
    EventFilter,
    EventStore,
    StoredEvent,
)

logger = logging.getLogger(__name__)


class MemoryAcknowledger(EventAcknowledger):
    """Memory-specific event acknowledger."""
    
    def __init__(
        self,
        store: "MemoryEventStore",
        event: StoredEvent,
        consumer_group: str,
        consumer_name: str,
        pending_key: str
    ):
        self.store = store
        self.event = event
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.pending_key = pending_key
        self._acknowledged = False
        
    async def ack(self) -> None:
        """Acknowledge successful processing."""
        if self._acknowledged:
            return
            
        if self.pending_key in self.store._pending[self.consumer_group]:
            del self.store._pending[self.consumer_group][self.pending_key]
            self._acknowledged = True
            logger.debug(f"Acknowledged event {self.event.event_id}")
        else:
            raise AcknowledgmentError("Event not found in pending")
    
    async def nack(self, reason: Optional[str] = None) -> None:
        """Negative acknowledgment - update error and increment delivery count."""
        if self.pending_key in self.store._pending[self.consumer_group]:
            pending = self.store._pending[self.consumer_group][self.pending_key]
            pending["delivery_count"] += 1
            pending["last_error"] = reason
            pending["last_attempt"] = datetime.now()
            
            if reason:
                logger.warning(f"NACK event {self.event.event_id}: {reason}")
    
    async def extend_timeout(self, seconds: int) -> None:
        """Extend processing timeout."""
        if self.pending_key in self.store._pending[self.consumer_group]:
            pending = self.store._pending[self.consumer_group][self.pending_key]
            pending["timeout_at"] = datetime.now() + timedelta(seconds=seconds)


class MemoryEventStore(EventStore):
    """In-memory implementation of event store."""
    
    def __init__(self, max_events: int = 10000):
        """Initialize memory event store.
        
        Args:
            max_events: Maximum events to keep per type
        """
        self.max_events = max_events
        self._events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_events))
        self._all_events: deque = deque(maxlen=max_events * 10)
        self._positions: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._pending: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._dlq: deque = deque(maxlen=max_events)
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
        self._connected = False
        
    async def connect(self) -> None:
        """Establish connection (no-op for memory store)."""
        self._connected = True
        logger.info("Connected to memory event store")
        
    async def disconnect(self) -> None:
        """Close connection (cleanup tasks)."""
        # Cancel all consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._consumer_tasks:
            await asyncio.gather(
                *self._consumer_tasks.values(),
                return_exceptions=True
            )
            
        self._connected = False
        
    async def append(self, event: BaseEvent) -> str:
        """Append an event to the store."""
        stream_id = f"{int(datetime.now().timestamp() * 1000000)}-{uuid.uuid4().hex[:8]}"
        event_data = event.to_dict()
        
        stored = StoredEvent(
            event_id=event_data["event_id"],
            event_type=event_data["event_type"],
            event_data=event_data,
            timestamp=datetime.fromisoformat(event_data["timestamp"]),
            stream_id=stream_id
        )
        
        # Store by type and in global stream
        self._events[event.event_type].append(stored)
        self._all_events.append(stored)
        
        logger.debug(f"Appended event {event.event_id} with stream_id {stream_id}")
        return stream_id
        
    async def get_event(self, stream_id: str) -> Optional[StoredEvent]:
        """Get a single event by its stream ID."""
        for event in self._all_events:
            if event.stream_id == stream_id:
                return event
        return None
        
    async def query(self, filter: EventFilter) -> List[StoredEvent]:
        """Query events based on filter criteria."""
        # Determine which events to search
        if filter.event_types:
            candidates = []
            for event_type in filter.event_types:
                candidates.extend(self._events[event_type])
        else:
            candidates = list(self._all_events)
            
        # Apply filters
        results = []
        for event in candidates:
            # Time filters
            if filter.start_time and event.timestamp < filter.start_time:
                continue
            if filter.end_time and event.timestamp > filter.end_time:
                continue
                
            # ID filters
            if filter.start_id and event.stream_id < filter.start_id:
                continue
            if filter.end_id and event.stream_id > filter.end_id:
                continue
                
            # Source filter
            if filter.source_pattern:
                source = event.event_data.get("source", "")
                if filter.source_pattern not in source:
                    continue
                    
            results.append(event)
            
            if filter.limit and len(results) >= filter.limit:
                break
                
        return results
        
    async def subscribe(
        self,
        config: ConsumerConfig,
        handler: Callable[[ConsumedEvent], Any]
    ) -> asyncio.Task:
        """Subscribe to events with at-least-once delivery."""
        
        async def consumer_loop():
            """Main consumer loop."""
            while True:
                try:
                    # Get events to process
                    events_to_process = []
                    
                    for event_type in config.event_types:
                        # Get last position
                        last_id = self._positions[config.consumer_group].get(event_type, "")
                        
                        # Find new events
                        for event in self._events[event_type]:
                            if event.stream_id > last_id:
                                # Check if already pending
                                pending_key = f"{event.stream_id}:{config.consumer_group}"
                                if pending_key not in self._pending[config.consumer_group]:
                                    events_to_process.append(event)
                                    
                                    if len(events_to_process) >= config.batch_size:
                                        break
                                        
                    # Also check for timed-out pending events
                    now = datetime.now()
                    for pending_key, pending in list(self._pending[config.consumer_group].items()):
                        if pending["timeout_at"] < now:
                            events_to_process.append(pending["event"])
                            
                    if not events_to_process:
                        # No events, wait a bit
                        await asyncio.sleep(config.block_timeout_ms / 1000)
                        continue
                        
                    # Process events
                    for event in events_to_process[:config.batch_size]:
                        pending_key = f"{event.stream_id}:{config.consumer_group}"
                        
                        # Get or create pending entry
                        if pending_key not in self._pending[config.consumer_group]:
                            self._pending[config.consumer_group][pending_key] = {
                                "event": event,
                                "consumer_name": config.consumer_name,
                                "claimed_at": datetime.now(),
                                "timeout_at": datetime.now() + timedelta(seconds=300),
                                "delivery_count": 1,
                                "last_error": None,
                                "last_attempt": None
                            }
                        
                        pending = self._pending[config.consumer_group][pending_key]
                        
                        # Create acknowledger
                        ack = MemoryAcknowledger(
                            self,
                            event,
                            config.consumer_group,
                            config.consumer_name,
                            pending_key
                        )
                        
                        # Create consumed event
                        consumed = ConsumedEvent(
                            event=event,
                            ack=ack,
                            delivery_count=pending["delivery_count"],
                            last_error=pending["last_error"]
                        )
                        
                        # Handle event
                        try:
                            await handler(consumed)
                            
                            # Update position on success
                            self._positions[config.consumer_group][event.event_type] = event.stream_id
                        except Exception as e:
                            logger.error(f"Handler error for event {event.event_id}: {e}")
                            
                            # Check if should move to DLQ
                            if pending["delivery_count"] >= config.dead_letter_after:
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
        
    async def get_pending_events(
        self,
        consumer_group: str,
        max_idle_ms: int = 60000
    ) -> List[ConsumedEvent]:
        """Get events that have been pending for too long."""
        events = []
        cutoff = datetime.now() - timedelta(milliseconds=max_idle_ms)
        
        for pending_key, pending in self._pending[consumer_group].items():
            if pending["claimed_at"] < cutoff:
                # Create acknowledger
                ack = MemoryAcknowledger(
                    self,
                    pending["event"],
                    consumer_group,
                    pending["consumer_name"],
                    pending_key
                )
                
                events.append(ConsumedEvent(
                    event=pending["event"],
                    ack=ack,
                    delivery_count=pending["delivery_count"],
                    last_error=pending["last_error"]
                ))
                
        return events
        
    async def move_to_dlq(
        self,
        event: ConsumedEvent,
        reason: str
    ) -> None:
        """Move an event to the dead letter queue."""
        self._dlq.append({
            "event": event.event,
            "reason": reason,
            "time": datetime.now(),
            "delivery_count": event.delivery_count
        })
        
        logger.info(f"Moved event {event.event.event_id} to DLQ: {reason}")
        
    async def replay_dlq(
        self,
        consumer_group: str,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Replay events from dead letter queue."""
        replayed = 0
        
        # Get events to replay
        to_replay = []
        for dlq_entry in list(self._dlq):
            if event_types and dlq_entry["event"].event_type not in event_types:
                continue
            to_replay.append(dlq_entry)
            
        # Re-add to streams
        for dlq_entry in to_replay:
            event = dlq_entry["event"]
            self._events[event.event_type].append(event)
            self._all_events.append(event)
            self._dlq.remove(dlq_entry)
            replayed += 1
            
        logger.info(f"Replayed {replayed} events from DLQ")
        return replayed
        
    async def get_stream_info(self) -> Dict[str, Any]:
        """Get information about the event streams."""
        info = {
            "backend": "memory",
            "events": {},
            "total_events": len(self._all_events),
            "pending_events": sum(len(p) for p in self._pending.values()),
            "dlq_events": len(self._dlq)
        }
        
        for event_type, events in self._events.items():
            info["events"][event_type] = len(events)
            
        return info
        
    async def trim_old_events(
        self,
        max_age_days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> int:
        """Remove events older than specified age."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        trimmed = 0
        
        # Trim type-specific streams
        types_to_trim = event_types or list(self._events.keys())
        for event_type in types_to_trim:
            events = self._events[event_type]
            original_len = len(events)
            
            # Remove old events
            self._events[event_type] = deque(
                (e for e in events if e.timestamp >= cutoff),
                maxlen=self.max_events
            )
            
            trimmed += original_len - len(self._events[event_type])
            
        # Rebuild all_events
        self._all_events.clear()
        for events in self._events.values():
            self._all_events.extend(events)
            
        logger.info(f"Trimmed {trimmed} events older than {max_age_days} days")
        return trimmed