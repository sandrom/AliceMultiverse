"""Event schema versioning and migration support.

This module provides tools for handling event schema evolution,
including version tracking, migration functions, and compatibility checks.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from .base import BaseEvent

logger = logging.getLogger(__name__)


@dataclass
class EventVersion:
    """Represents a version of an event schema."""
    version: int
    description: str
    deprecated: bool = False
    deprecated_since: Optional[str] = None
    removal_version: Optional[int] = None


class EventMigration(ABC):
    """Abstract base class for event migrations."""
    
    @property
    @abstractmethod
    def from_version(self) -> int:
        """Source version for this migration."""
        pass
    
    @property
    @abstractmethod
    def to_version(self) -> int:
        """Target version for this migration."""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Event type this migration applies to."""
        pass
    
    @abstractmethod
    def migrate(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate event data from source to target version.
        
        Args:
            event_data: Event data in source version format
            
        Returns:
            Event data in target version format
            
        Raises:
            ValueError: If migration fails
        """
        pass
    
    @abstractmethod
    def can_migrate(self, event_data: Dict[str, Any]) -> bool:
        """Check if this migration can handle the event data.
        
        Args:
            event_data: Event data to check
            
        Returns:
            True if migration can proceed
        """
        pass


class EventVersionRegistry:
    """Registry for event versions and migrations."""
    
    def __init__(self):
        self._versions: Dict[str, Dict[int, EventVersion]] = {}
        self._migrations: Dict[str, List[EventMigration]] = {}
        self._current_versions: Dict[str, int] = {}
        
    def register_version(
        self,
        event_type: str,
        version: EventVersion
    ) -> None:
        """Register an event version.
        
        Args:
            event_type: Type of event
            version: Version information
        """
        if event_type not in self._versions:
            self._versions[event_type] = {}
            
        self._versions[event_type][version.version] = version
        
        # Update current version if this is newer
        if event_type not in self._current_versions or version.version > self._current_versions[event_type]:
            if not version.deprecated:
                self._current_versions[event_type] = version.version
                
        logger.debug(f"Registered version {version.version} for {event_type}")
        
    def register_migration(
        self,
        migration: EventMigration
    ) -> None:
        """Register an event migration.
        
        Args:
            migration: Migration instance
        """
        event_type = migration.event_type
        
        if event_type not in self._migrations:
            self._migrations[event_type] = []
            
        self._migrations[event_type].append(migration)
        
        # Sort by from_version to ensure proper order
        self._migrations[event_type].sort(key=lambda m: m.from_version)
        
        logger.debug(
            f"Registered migration for {event_type} "
            f"from v{migration.from_version} to v{migration.to_version}"
        )
        
    def get_current_version(self, event_type: str) -> int:
        """Get current version for an event type.
        
        Args:
            event_type: Type of event
            
        Returns:
            Current version number
        """
        return self._current_versions.get(event_type, 1)
        
    def migrate_event(
        self,
        event_data: Dict[str, Any],
        target_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Migrate event data to target version.
        
        Args:
            event_data: Event data with version field
            target_version: Target version (None for current)
            
        Returns:
            Migrated event data
            
        Raises:
            ValueError: If migration path not found
        """
        event_type = event_data.get("event_type")
        if not event_type:
            raise ValueError("Event data missing event_type")
            
        current_version = event_data.get("version", 1)
        target = target_version or self.get_current_version(event_type)
        
        if current_version == target:
            return event_data
            
        if current_version > target:
            raise ValueError(
                f"Cannot downgrade event from v{current_version} to v{target}"
            )
            
        # Find migration path
        migrations = self._find_migration_path(
            event_type,
            current_version,
            target
        )
        
        if not migrations:
            raise ValueError(
                f"No migration path found for {event_type} "
                f"from v{current_version} to v{target}"
            )
            
        # Apply migrations in sequence
        migrated_data = event_data.copy()
        for migration in migrations:
            if not migration.can_migrate(migrated_data):
                raise ValueError(
                    f"Migration from v{migration.from_version} "
                    f"to v{migration.to_version} cannot handle event data"
                )
                
            migrated_data = migration.migrate(migrated_data)
            migrated_data["version"] = migration.to_version
            
            logger.debug(
                f"Migrated {event_type} from "
                f"v{migration.from_version} to v{migration.to_version}"
            )
            
        return migrated_data
        
    def _find_migration_path(
        self,
        event_type: str,
        from_version: int,
        to_version: int
    ) -> List[EventMigration]:
        """Find migration path between versions.
        
        Args:
            event_type: Type of event
            from_version: Starting version
            to_version: Target version
            
        Returns:
            List of migrations to apply in order
        """
        if event_type not in self._migrations:
            return []
            
        migrations = self._migrations[event_type]
        path = []
        current = from_version
        
        while current < to_version:
            # Find migration from current version
            found = False
            for migration in migrations:
                if migration.from_version == current:
                    path.append(migration)
                    current = migration.to_version
                    found = True
                    break
                    
            if not found:
                # No direct migration, path incomplete
                return []
                
        return path


# Global registry instance
_version_registry = EventVersionRegistry()


def get_version_registry() -> EventVersionRegistry:
    """Get global version registry."""
    return _version_registry


# Decorator for versioned events
def versioned_event(version: int, event_type: str, description: str):
    """Decorator to mark an event class with version information.
    
    Args:
        version: Version number
        event_type: Event type identifier
        description: Version description
    """
    def decorator(cls: Type[BaseEvent]) -> Type[BaseEvent]:
        # Register version
        _version_registry.register_version(
            event_type,
            EventVersion(version=version, description=description)
        )
        
        # Add version info to class
        cls._schema_version = version
        cls._event_type = event_type
        
        # Override to_dict to include version
        original_to_dict = cls.to_dict
        
        def to_dict_with_version(self) -> Dict[str, Any]:
            data = original_to_dict(self)
            data["version"] = version
            return data
            
        cls.to_dict = to_dict_with_version
        
        return cls
        
    return decorator


# Example migrations for asset events
class AssetDiscoveredV1ToV2(EventMigration):
    """Migrate AssetDiscoveredEvent from v1 to v2.
    
    Changes:
    - Add 'tags' field (empty list by default)
    - Rename 'path' to 'file_path' for consistency
    """
    
    @property
    def from_version(self) -> int:
        return 1
    
    @property
    def to_version(self) -> int:
        return 2
    
    @property
    def event_type(self) -> str:
        return "asset.discovered"
    
    def migrate(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        migrated = event_data.copy()
        
        # Add tags field
        if "tags" not in migrated:
            migrated["tags"] = []
            
        # Rename path to file_path
        if "path" in migrated:
            migrated["file_path"] = migrated.pop("path")
            
        return migrated
    
    def can_migrate(self, event_data: Dict[str, Any]) -> bool:
        # Can migrate if it's v1 format (has 'path' field)
        return event_data.get("version", 1) == 1


class QualityAssessedV1ToV2(EventMigration):
    """Migrate QualityAssessedEvent from v1 to v2.
    
    Changes:
    - Add 'provider' field to track which quality provider was used
    - Add 'confidence' field for score confidence
    - Restructure 'details' to be provider-specific
    """
    
    @property
    def from_version(self) -> int:
        return 1
    
    @property
    def to_version(self) -> int:
        return 2
    
    @property
    def event_type(self) -> str:
        return "quality.assessed"
    
    def migrate(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        migrated = event_data.copy()
        
        # Add provider field (assume BRISQUE for v1)
        if "provider" not in migrated:
            migrated["provider"] = "brisque"
            
        # Add confidence field
        if "confidence" not in migrated:
            migrated["confidence"] = 0.8  # Default confidence
            
        # Restructure details if present
        if "details" in migrated and not isinstance(migrated["details"], dict):
            # Old format was a list, convert to dict
            old_details = migrated["details"]
            migrated["details"] = {
                "brisque": {
                    "raw_score": migrated.get("score", 0),
                    "details": old_details if isinstance(old_details, list) else []
                }
            }
            
        return migrated
    
    def can_migrate(self, event_data: Dict[str, Any]) -> bool:
        return event_data.get("version", 1) == 1


# Helper function to migrate events in batch
async def migrate_events_batch(
    events: List[Dict[str, Any]],
    target_version: Optional[int] = None,
    registry: Optional[EventVersionRegistry] = None
) -> List[Dict[str, Any]]:
    """Migrate a batch of events to target version.
    
    Args:
        events: List of event data
        target_version: Target version (None for current)
        registry: Version registry to use (None for global)
        
    Returns:
        List of migrated events
    """
    if registry is None:
        registry = get_version_registry()
        
    migrated = []
    for event in events:
        try:
            migrated.append(registry.migrate_event(event, target_version))
        except ValueError as e:
            logger.warning(f"Failed to migrate event {event.get('event_id')}: {e}")
            # Keep original if migration fails
            migrated.append(event)
            
    return migrated


# Register example migrations
def register_default_migrations():
    """Register default event migrations."""
    registry = get_version_registry()
    
    # Asset event versions
    registry.register_version(
        "asset.discovered",
        EventVersion(1, "Initial version")
    )
    registry.register_version(
        "asset.discovered",
        EventVersion(2, "Added tags and renamed path field")
    )
    
    # Quality event versions
    registry.register_version(
        "quality.assessed",
        EventVersion(1, "Initial version")
    )
    registry.register_version(
        "quality.assessed",
        EventVersion(2, "Added provider tracking and confidence")
    )
    
    # Register migrations
    registry.register_migration(AssetDiscoveredV1ToV2())
    registry.register_migration(QualityAssessedV1ToV2())


# Initialize default migrations on import
register_default_migrations()