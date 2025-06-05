"""Base event definitions for the event system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


class Event(ABC):
    """Base class for all events."""
    
    def __init__(self):
        """Initialize event metadata."""
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.source = "alice"
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type string."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
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