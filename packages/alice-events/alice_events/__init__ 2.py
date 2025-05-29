"""Alice Events - Shared event infrastructure for AliceMultiverse."""

from .base_v2 import (
    BaseEvent,
    EventBus,
    EventSubscriber,
    get_event_bus,
    publish_event,
    create_event
)

# For backward compatibility
global_event_bus = get_event_bus()

from .asset_events_v2 import (
    AssetDiscoveredEvent,
    AssetProcessedEvent,
    AssetOrganizedEvent,
    QualityAssessedEvent,
    MetadataUpdatedEvent
)

from .creative_events_v2 import (
    ProjectCreatedEvent,
    StyleChosenEvent,
    ContextUpdatedEvent,
    CharacterDefinedEvent,
    ConceptApprovedEvent
)

from .workflow_events_v2 import (
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent
)

# Optional persistence support
try:
    from .persistence import EventPersistence, get_persistence, REDIS_AVAILABLE
    from .base_v2_persistence import (
        PersistentEventBus,
        persistent_event_bus,
        publish_persistent_event,
        monitor_events_from_redis
    )
except ImportError:
    REDIS_AVAILABLE = False

__all__ = [
    # Base classes
    "BaseEvent",
    "EventBus", 
    "EventSubscriber",
    "global_event_bus",
    "publish_event",
    "create_event",
    
    # Asset events
    "AssetDiscoveredEvent",
    "AssetProcessedEvent",
    "AssetOrganizedEvent",
    "QualityAssessedEvent",
    "MetadataUpdatedEvent",
    
    # Creative events
    "ProjectCreatedEvent",
    "StyleChosenEvent",
    "ContextUpdatedEvent",
    "CharacterDefinedEvent",
    "ConceptApprovedEvent",
    
    # Workflow events
    "WorkflowStartedEvent",
    "WorkflowStepCompletedEvent",
    "WorkflowCompletedEvent",
    "WorkflowFailedEvent",
    
    # Persistence (optional)
    "REDIS_AVAILABLE",
]

if REDIS_AVAILABLE:
    __all__.extend([
        "EventPersistence",
        "get_persistence",
        "PersistentEventBus",
        "persistent_event_bus",
        "publish_persistent_event",
        "monitor_events_from_redis"
    ])