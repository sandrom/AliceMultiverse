# Redis Removal Plan for AliceMultiverse

## Overview
This plan outlines the steps to remove Redis dependency from AliceMultiverse while maintaining all functionality. The system will use a simple file-based event log as a temporary replacement, making it easy to re-add Redis later when microservices are needed.

## Current Redis Usage

### 1. Event System (Primary Usage)
- **Location**: `alicemultiverse/events/redis_streams.py`
- **Purpose**: Publishing and subscribing to events using Redis Streams
- **Used by**:
  - Providers (publish generation events)
  - Project/Selection services (publish workflow events)
  - Asset processor service
  - Alice orchestrator

### 2. Database Cache (Secondary Usage)
- **Location**: `alicemultiverse/database/cache.py`
- **Purpose**: Caching search results and embeddings
- **Status**: Appears to be optional/unused in current implementation

## Implementation Strategy

### Phase 1: Create File-Based Event System

Create a new file-based event system that mimics the Redis Streams API:

```python
# alicemultiverse/events/file_events.py
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from threading import Lock
from datetime import datetime, timezone

class FileBasedEventSystem:
    """Simple file-based event system for local development."""
    
    def __init__(self, event_log_dir: Optional[Path] = None):
        self.event_log_dir = event_log_dir or Path.home() / ".alice" / "events"
        self.event_log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._listeners: Dict[str, List[Callable]] = {}
        
    def publish_sync(self, event_type: str, data: Dict[str, Any]) -> str:
        """Publish event synchronously to file."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        event = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "timestamp": timestamp
        }
        
        # Write to daily log file
        log_file = self.event_log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with self._lock:
            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
                
        # Call local listeners (for same-process subscriptions)
        self._notify_listeners(event_type, event)
        
        return event_id
        
    async def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """Async wrapper for compatibility."""
        return self.publish_sync(event_type, data)
```

### Phase 2: Create Adapter Layer

Create an adapter that provides the same interface as Redis but uses the file system:

```python
# alicemultiverse/events/adapter.py
import os
from typing import Optional

def get_event_system():
    """Get appropriate event system based on environment."""
    if os.getenv("USE_REDIS_EVENTS", "false").lower() == "true":
        from .redis_streams import RedisStreamsEventSystem
        return RedisStreamsEventSystem()
    else:
        from .file_events import FileBasedEventSystem
        return FileBasedEventSystem()

# Convenience functions maintain the same API
publish_event_sync = lambda event_type, data: get_event_system().publish_sync(event_type, data)
```

## Files to Modify

### 1. Core Event System Files

#### a. Create new file-based implementation
- **New file**: `alicemultiverse/events/file_events.py`
- **Action**: Implement FileBasedEventSystem class

#### b. Update event module initialization
- **File**: `alicemultiverse/events/__init__.py`
- **Changes**:
  ```python
  # Add conditional import based on environment
  import os
  
  if os.getenv("USE_REDIS_EVENTS", "false").lower() == "true":
      from .redis_streams import (
          RedisStreamsEventSystem,
          get_event_system,
          publish_event,
          publish_event_sync,
          subscribe_to_events,
      )
  else:
      from .file_events import (
          FileBasedEventSystem as RedisStreamsEventSystem,
          get_event_system,
          publish_event,
          publish_event_sync,
          subscribe_to_events,
      )
  ```

### 2. Provider Files (No changes needed!)
These files import from `alicemultiverse.events` and will automatically use the new system:
- `alicemultiverse/providers/provider.py`
- `alicemultiverse/providers/hedra_provider.py`
- `alicemultiverse/providers/midjourney_provider.py`

### 3. Service Files (No changes needed!)
- `alicemultiverse/projects/service.py`
- `alicemultiverse/projects/file_service.py`
- `alicemultiverse/selections/service.py`
- `alicemultiverse/interface/alice_orchestrator.py`

### 4. Update Requirements
- **File**: `requirements.txt`
- **Change**: Move `redis>=5.0.0` to a new `requirements-redis.txt` file

### 5. Configuration Updates
- **File**: `alicemultiverse/core/config.py`
- **Add**: Configuration for event system selection

### 6. Test Files
- **Files to update**:
  - `tests/unit/test_redis_streams.py` → Skip if Redis not available
  - `tests/unit/test_all_event_types.py` → Should work with both systems
  - `tests/conftest.py` → Add fixture for file-based events

### 7. Documentation Updates
- Update `CLAUDE.md` to mention the file-based event system
- Update installation docs to make Redis optional

## Error Handling Strategy

The current code doesn't handle Redis connection errors, which is why we need this change. The file-based system will:

1. **Never fail on publish**: File writes are local and reliable
2. **Graceful degradation**: If file write fails, log error but don't crash
3. **No network dependencies**: Everything runs locally

## Migration Path

### To Remove Redis:
1. Set environment variable: `USE_REDIS_EVENTS=false` (or make it default)
2. System automatically uses file-based events
3. No code changes needed in providers or services

### To Re-enable Redis Later:
1. Set environment variable: `USE_REDIS_EVENTS=true`
2. Ensure Redis is running
3. System automatically uses Redis Streams

## Benefits of This Approach

1. **Minimal code changes**: Only the event system internals change
2. **Same API**: All existing code continues to work
3. **Easy rollback**: Just change an environment variable
4. **Local development friendly**: No external services needed
5. **Event history**: Files provide a simple audit trail
6. **Future-proof**: Easy to add Redis back for production

## Implementation Order

1. **Create file_events.py** with basic publish functionality
2. **Update __init__.py** to conditionally import
3. **Update requirements.txt** to make Redis optional
4. **Add tests** for file-based events
5. **Update documentation**
6. **Test with existing code** - should work without changes

## Notes

- The file-based system is perfect for a personal tool
- Events are still logged for debugging/audit purposes  
- When microservices are added later, just set USE_REDIS_EVENTS=true
- Consider adding event cleanup (delete old log files) later
- The database/cache.py Redis usage can be ignored - it's not actively used