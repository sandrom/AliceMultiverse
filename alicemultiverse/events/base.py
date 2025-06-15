"""Base event definitions for the event system."""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class Event(ABC):
    """Base class for all events."""

    def __init__(self):
        """Initialize event metadata."""
        # Use timestamp-based event ID for easier debugging
        self.event_id = f"evt_{int(time.time() * 1000000)}"
        self.timestamp = datetime.utcnow()
        self.source = "alice"

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type string."""

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }

        # Add all other fields
        for field_name in self.__dataclass_fields__:
            if field_name not in ["event_id", "timestamp", "source"]:
                value = getattr(self, field_name)
                # Handle special types
                if hasattr(value, "isoformat"):  # datetime
                    data[field_name] = value.isoformat()
                elif hasattr(value, "__dict__"):  # objects
                    data[field_name] = str(value)
                else:
                    data[field_name] = value

        return data
