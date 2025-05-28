"""Event middleware for cross-cutting concerns.

Provides logging, monitoring, persistence, and other middleware
that can be applied to all events flowing through the system.
"""

import json
import logging
import time
from collections.abc import Callable
from datetime import UTC,  datetime
from pathlib import Path
from typing import Any

from .base import BaseEvent

logger = logging.getLogger(__name__)


class EventLogger:
    """Middleware that logs all events for debugging and auditing."""

    def __init__(self, log_level: int = logging.DEBUG):
        self.log_level = log_level

    def __call__(self, event: BaseEvent) -> None:
        """Log the event."""
        logger.log(
            self.log_level,
            f"Event: {event.event_type} | "
            f"ID: {event.event_id} | "
            f"Source: {event.source} | "
            f"Time: {event.timestamp.isoformat()}",
        )

        # Log full event in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Event data: {json.dumps(event.to_dict(), indent=2)}")


class EventMetrics:
    """Middleware that collects metrics about events."""

    def __init__(self):
        self.event_counts: dict[str, int] = {}
        self.event_timings: dict[str, list] = {}
        self.start_time = time.time()

    def __call__(self, event: BaseEvent) -> None:
        """Record metrics for the event."""
        # Count events by type
        self.event_counts[event.event_type] = self.event_counts.get(event.event_type, 0) + 1

        # Track timing between events of same type
        now = time.time()
        if event.event_type not in self.event_timings:
            self.event_timings[event.event_type] = []
        self.event_timings[event.event_type].append(now)

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics."""
        total_events = sum(self.event_counts.values())
        runtime = time.time() - self.start_time

        stats = {
            "total_events": total_events,
            "events_per_second": total_events / runtime if runtime > 0 else 0,
            "runtime_seconds": runtime,
            "event_counts": self.event_counts.copy(),
            "event_types": list(self.event_counts.keys()),
        }

        # Calculate average time between events of same type
        avg_intervals = {}
        for event_type, timings in self.event_timings.items():
            if len(timings) > 1:
                intervals = [timings[i] - timings[i - 1] for i in range(1, len(timings))]
                avg_intervals[event_type] = sum(intervals) / len(intervals)
        stats["average_intervals"] = avg_intervals

        return stats


class EventPersistence:
    """Middleware that persists events to disk for replay and debugging."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectory for current session
        session_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.storage_dir / session_id
        self.session_dir.mkdir(exist_ok=True)

    def __call__(self, event: BaseEvent) -> None:
        """Persist the event to disk."""
        try:
            # Group events by type
            type_dir = self.session_dir / event.event_type.replace(".", "_")
            type_dir.mkdir(exist_ok=True)

            # Save event as JSON
            filename = f"{event.timestamp.strftime('%Y%m%d_%H%M%S')}_{event.event_id}.json"
            event_file = type_dir / filename

            with open(event_file, "w") as f:
                json.dump(event.to_dict(), f, indent=2)

        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {e}")


class EventFilter:
    """Middleware that filters events based on criteria."""

    def __init__(
        self,
        include_types: list | None = None,
        exclude_types: list | None = None,
        predicate: Callable[[BaseEvent], bool] | None = None,
    ):
        self.include_types = set(include_types) if include_types else None
        self.exclude_types = set(exclude_types) if exclude_types else None
        self.predicate = predicate
        self._filtered_count = 0

    def __call__(self, event: BaseEvent) -> None:
        """Check if event should be filtered."""
        # Check include list
        if self.include_types and event.event_type not in self.include_types:
            self._filtered_count += 1
            return

        # Check exclude list
        if self.exclude_types and event.event_type in self.exclude_types:
            self._filtered_count += 1
            return

        # Check custom predicate
        if self.predicate and not self.predicate(event):
            self._filtered_count += 1
            return

    @property
    def filtered_count(self) -> int:
        """Get count of filtered events."""
        return self._filtered_count


class EventDebugger:
    """Middleware for debugging event flow."""

    def __init__(self, break_on_types: list | None = None):
        self.break_on_types = set(break_on_types) if break_on_types else set()
        self.event_history: list = []
        self.max_history = 100

    def __call__(self, event: BaseEvent) -> None:
        """Debug the event."""
        # Add to history
        self.event_history.append(
            {
                "type": event.event_type,
                "id": event.event_id,
                "time": event.timestamp,
                "source": event.source,
            }
        )

        # Keep history bounded
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Break if requested
        if event.event_type in self.break_on_types:
            logger.warning(f"DEBUGGER: Breaking on event type {event.event_type}")
            # In production, this would integrate with a debugger
            # For now, just log the full event
            logger.warning(f"Event details: {json.dumps(event.to_dict(), indent=2)}")

    def get_recent_events(self, count: int = 10) -> list:
        """Get recent event history."""
        return self.event_history[-count:]
