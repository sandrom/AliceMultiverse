# alice-events

Shared event definitions and infrastructure for AliceMultiverse.

## Installation

```bash
pip install -e packages/alice-events
```

## Usage

```python
from alice_events import (
    AssetDiscoveredEvent,
    WorkflowStartedEvent,
    publish_event,
    EventBus,
    EventSubscriber
)

# Publish an event
event = AssetDiscoveredEvent(
    file_path="/path/to/image.jpg",
    content_hash="abc123",
    file_size=1024000,
    media_type="image",
    project_name="my-project"
)
await publish_event(event)

# Subscribe to events
class MySubscriber(EventSubscriber):
    def __init__(self):
        super().__init__(event_types=["asset.discovered"])
    
    async def handle_event(self, event):
        print(f"Asset discovered: {event.file_path}")
```

## Event Categories

- **Asset Events**: File discovery, processing, organization
- **Workflow Events**: Workflow lifecycle management
- **Creative Events**: Project and creative workflow events

## Persistence

Optional Redis Streams support for reliable event delivery:

```python
from alice_events.persistence import EventPersistence

persistence = EventPersistence()
await persistence.connect()
await persistence.persist_event(event)
```