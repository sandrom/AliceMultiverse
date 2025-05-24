# Event System Developer Guide

This guide helps developers work with the AliceMultiverse event system to add new features and integrate with existing functionality.

## Quick Start

### Subscribing to Events

Create a subscriber to react to system events:

```python
from alicemultiverse.events import EventSubscriber, Event

class MyFeatureSubscriber(EventSubscriber):
    @property
    def event_types(self):
        # Subscribe to specific events
        return ['asset.discovered', 'quality.assessed']
    
    async def handle_event(self, event: Event):
        if event.event_type == 'asset.discovered':
            print(f"New asset: {event.file_path}")
        elif event.event_type == 'quality.assessed':
            print(f"Quality: {event.star_rating} stars")

# Register the subscriber
from alicemultiverse.events import get_event_bus
bus = get_event_bus()
bus.subscribe(MyFeatureSubscriber())
```

### Publishing Events

Emit events when significant actions occur:

```python
from alicemultiverse.events import AssetDiscoveredEvent, publish_event

# When you discover a new asset
event = AssetDiscoveredEvent(
    source="MyFeature",
    file_path="/path/to/file.png",
    content_hash="abc123",
    file_size=1024000,
    media_type="image",
    project_name="my-project"
)

# Publish asynchronously
await publish_event(event)
```

## Event Catalog

### Asset Events

#### asset.discovered
Fired when a new asset is found:
```python
AssetDiscoveredEvent(
    file_path: str,
    content_hash: str,
    file_size: int,
    media_type: str,  # 'image' or 'video'
    project_name: str,
    source_type: Optional[str]
)
```

#### asset.processed
Fired after metadata extraction:
```python
AssetProcessedEvent(
    content_hash: str,
    file_path: str,
    metadata: Dict[str, Any],
    extracted_metadata: Dict[str, Any],
    generation_params: Dict[str, Any]
)
```

#### asset.organized
Fired when asset is moved/copied:
```python
AssetOrganizedEvent(
    content_hash: str,
    source_path: str,
    destination_path: str,
    project_name: str,
    source_type: str,
    date_folder: str,
    quality_folder: Optional[str]
)
```

#### quality.assessed
Fired after quality assessment:
```python
QualityAssessedEvent(
    content_hash: str,
    file_path: str,
    star_rating: int,  # 1-5
    brisque_score: Optional[float],
    sightengine_score: Optional[float],
    claude_assessment: Optional[Dict[str, Any]]
)
```

### Workflow Events

#### workflow.started
Fired when creative workflow begins:
```python
WorkflowStartedEvent(
    workflow_id: str,
    workflow_type: str,
    workflow_name: str,
    input_parameters: Dict[str, Any]
)
```

#### workflow.completed
Fired on successful completion:
```python
WorkflowCompletedEvent(
    workflow_id: str,
    output_assets: List[str],  # Content hashes
    total_duration_ms: int,
    total_cost: Optional[float]
)
```

### Creative Events

#### project.created
Fired when new project starts:
```python
ProjectCreatedEvent(
    project_id: str,
    project_name: str,
    initial_context: Dict[str, Any],
    style_preferences: Dict[str, Any]
)
```

#### context.updated
Fired when creative context changes:
```python
ContextUpdatedEvent(
    project_id: str,
    context_type: str,
    update_type: str,  # 'addition', 'modification', 'removal'
    new_value: Dict[str, Any]
)
```

## Best Practices

### 1. Event Design

Events should be:
- **Immutable**: Once published, never change
- **Self-contained**: Include all needed data
- **Domain-focused**: Use business language

```python
# Good: Domain event
AssetQualityImprovedEvent(rating=5)

# Bad: Technical event  
DatabaseRecordUpdatedEvent(table="assets")
```

### 2. Error Handling

Subscribers should handle errors gracefully:

```python
async def handle_event(self, event: Event):
    try:
        await self.process_event(event)
    except Exception as e:
        logger.error(f"Failed to process {event.event_type}: {e}")
        # Don't re-raise - let other subscribers continue
```

### 3. Performance

For heavy processing, use background tasks:

```python
async def handle_event(self, event: Event):
    # Quick validation
    if not self.should_process(event):
        return
    
    # Heavy work in background
    asyncio.create_task(self.process_async(event))
```

## Testing Events

### Unit Testing

Test subscribers in isolation:

```python
import pytest
from alicemultiverse.events import AssetDiscoveredEvent

@pytest.mark.asyncio
async def test_subscriber():
    subscriber = MyFeatureSubscriber()
    event = AssetDiscoveredEvent(
        source="test",
        file_path="/test.png",
        content_hash="test123",
        file_size=1000,
        media_type="image",
        project_name="test"
    )
    
    await subscriber.handle_event(event)
    # Assert expected behavior
```

### Integration Testing

Test with real event bus:

```python
@pytest.mark.asyncio
async def test_event_flow():
    bus = EventBus()
    subscriber = MyFeatureSubscriber()
    bus.subscribe(subscriber)
    
    event = AssetDiscoveredEvent(...)
    await bus.publish(event)
    
    # Verify subscriber was called
```

## Monitoring

Use the event monitor during development:

```bash
# Basic monitoring
python scripts/event_monitor.py

# With full details
python scripts/event_monitor.py --verbose

# Save to disk for analysis
python scripts/event_monitor.py --persist
```

## Adding New Events

1. Define event class in appropriate module:
```python
# In alicemultiverse/events/your_events.py
@dataclass
class YourNewEvent(Event):
    # Event fields
    important_data: str
    
    @property
    def event_type(self) -> str:
        return "your.event_type"
```

2. Export from events module:
```python
# In alicemultiverse/events/__init__.py
from .your_events import YourNewEvent
__all__.append('YourNewEvent')
```

3. Document in AsyncAPI:
```yaml
# In asyncapi/asyncapi.yaml
YourNewEvent:
  name: YourNewEvent
  title: Your New Event
  summary: What this event represents
  payload:
    $ref: '#/components/schemas/YourNewEventPayload'
```

## Migration Guide

### From Direct Calls to Events

Before:
```python
def process_file(self, file_path):
    # Direct processing
    metadata = extract_metadata(file_path)
    quality = assess_quality(file_path)
    organize_file(file_path, quality)
```

After:
```python
async def process_file(self, file_path):
    # Publish discovery event
    await publish_event(AssetDiscoveredEvent(...))
    # Let subscribers handle the rest
```

### From Callbacks to Subscribers

Before:
```python
organizer.on_complete = my_callback
```

After:
```python
class CompletionSubscriber(EventSubscriber):
    @property
    def event_types(self):
        return ['asset.organized']
    
    async def handle_event(self, event):
        # Handle completion
```

## Future: Service Communication

When services are extracted, events will flow through Dapr:

```python
# Today: In-memory
await publish_event(event)

# Future: Through Dapr (no code change!)
await publish_event(event)  # Dapr handles routing
```

The event system is designed to evolve without breaking existing code.