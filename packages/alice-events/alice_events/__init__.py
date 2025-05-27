"""Alice Events - Shared event infrastructure for AliceMultiverse."""

from .base_v2 import (
    BaseEvent,
    EventBus,
    EventSubscriber,
    create_event,
    get_event_bus,
    publish_event,
)

# For backward compatibility
global_event_bus = get_event_bus()

from .asset_events_v2 import (
    AssetDiscoveredEvent,
    AssetOrganizedEvent,
    AssetProcessedEvent,
    MetadataUpdatedEvent,
    QualityAssessedEvent,
)
from .creative_events_v2 import (
    CharacterDefinedEvent,
    ConceptApprovedEvent,
    ContextUpdatedEvent,
    ProjectCreatedEvent,
    StyleChosenEvent,
)
from .workflow_events_v2 import (
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
)

# Optional persistence support
try:
    from .base_v2_persistence import (
        PersistentEventBus,
        monitor_events_from_redis,
        persistent_event_bus,
        publish_persistent_event,
    )
    from .persistence import REDIS_AVAILABLE, EventPersistence, get_persistence
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
    __all__.extend(
        [
            "EventPersistence",
            "PersistentEventBus",
            "get_persistence",
            "monitor_events_from_redis",
            "persistent_event_bus",
            "publish_persistent_event",
        ]
    )
