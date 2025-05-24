# Event System V2 Documentation

## Overview

The AliceMultiverse event system has been refactored to version 2 to address Python dataclass inheritance limitations. The new version uses composition over inheritance and provides a clean, extensible event infrastructure.

## Key Changes from V1 to V2

### 1. Dataclass Inheritance Fix

**Problem**: Python dataclasses don't allow parent classes with default values when child classes have required fields.

**Solution**: 
- Base class (`BaseEvent`) is no longer a dataclass
- Metadata fields are added via `with_metadata()` method
- Event classes are standalone dataclasses that implement the `BaseEvent` interface

### 2. Simplified Structure

Events in V2 have a flatter structure:
- No nested `data` field
- All event fields are at the top level
- Metadata fields are added as properties

## Event Categories

### Asset Events
- `AssetDiscoveredEvent`: When new media files are found
- `AssetProcessedEvent`: When assets are processed/analyzed
- `AssetOrganizedEvent`: When assets are moved to organized folders
- `QualityAssessedEvent`: When quality assessment completes
- `MetadataUpdatedEvent`: When asset metadata changes

### Creative Events
- `ProjectCreatedEvent`: When a new creative project starts
- `StyleChosenEvent`: When a style is selected
- `ContextUpdatedEvent`: When project context changes
- `CharacterDefinedEvent`: When a character is defined
- `ConceptApprovedEvent`: When a concept is approved

### Workflow Events
- `WorkflowStartedEvent`: When a workflow begins
- `WorkflowStepCompletedEvent`: When a workflow step completes
- `WorkflowCompletedEvent`: When entire workflow finishes
- `WorkflowFailedEvent`: When a workflow encounters an error

## Usage Examples

### Publishing Events

```python
from alicemultiverse.events.asset_events_v2 import AssetDiscoveredEvent
from alicemultiverse.events.base import publish_event

# Create and publish an event
event = AssetDiscoveredEvent(
    file_path="/path/to/image.jpg",
    content_hash="abc123",
    file_size=1024000,
    media_type="image",
    project_name="my-project"
)
publish_event(event)
```

### Subscribing to Events

```python
from alicemultiverse.events.base import EventSubscriber, global_event_bus

class MySubscriber(EventSubscriber):
    def __init__(self):
        super().__init__(event_types=["asset.discovered", "asset.processed"])
    
    async def handle_event(self, event):
        print(f"Received: {event.event_type}")
        # Process the event

# Register subscriber
subscriber = MySubscriber()
global_event_bus.subscribe(subscriber)
```

### Event Metadata

All events include these metadata fields:
- `event_id`: Unique identifier (UUID)
- `event_type`: String identifier (e.g., "asset.discovered")
- `timestamp`: When the event occurred
- `version`: Event schema version (default: "1.0.0")
- `source`: Event source identifier

## Migration Guide

To migrate from V1 to V2:

1. Update imports from `*_events.py` to `*_events_v2.py`
2. Update field names to match V2 schemas
3. Remove references to nested `data` field
4. Update event type strings if changed

## Testing

Comprehensive tests ensure all event types work correctly:

```bash
# Run event system tests
pytest tests/unit/test_event_system.py -v

# Run comprehensive event type tests  
pytest tests/unit/test_all_event_types.py -v
```

## Next Steps

The event system provides the foundation for:
- Event persistence with Redis Streams
- Service extraction and microservices architecture
- Real-time monitoring and debugging
- Event-driven workflows and automation