"""Protocol definitions for type checking mixins and interfaces."""

from typing import Any, Protocol

from .config import Config
from .types import Statistics


class HasConfig(Protocol):
    """Protocol for objects that have a config attribute."""
    config: Config


class HasStats(Protocol):
    """Protocol for objects that track statistics."""
    stats: Statistics


class HasOrganizer(Protocol):
    """Protocol for objects that have an organizer."""
    organizer: Any  # Avoid circular import


class HasSearchDB(Protocol):
    """Protocol for objects with search database."""
    search_db: Any  # Avoid circular import


class HasMetadataCache(Protocol):
    """Protocol for objects with metadata cache."""
    metadata_cache: Any  # Avoid circular import


class HasSelectionService(Protocol):
    """Protocol for objects with selection service."""
    selection_service: Any  # Avoid circular import


class HasProjectService(Protocol):
    """Protocol for objects with project service."""
    project_service: Any  # Avoid circular import


class HasUnderstandingProvider(Protocol):
    """Protocol for objects with understanding provider."""
    understanding_provider: Any  # Avoid circular import


class HasSearchHandler(Protocol):
    """Protocol for objects with search handler."""
    search_handler: Any  # Avoid circular import


class HasServer(Protocol):
    """Protocol for MCP server objects."""
    def tool(self, *args, **kwargs) -> Any: ...


# Combined protocols for complex mixins
class OrganizerBase(HasConfig, HasStats, Protocol):
    """Base protocol for organizer mixins."""
    pass


class InterfaceBase(HasConfig, HasOrganizer, HasSearchHandler, Protocol):
    """Base protocol for interface mixins."""
    pass


class WorkflowBase(HasSearchDB, HasUnderstandingProvider, Protocol):
    """Base protocol for workflow mixins."""
    pass