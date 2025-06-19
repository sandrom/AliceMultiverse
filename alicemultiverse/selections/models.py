"""Models for selection tracking system."""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class SelectionStatus(str, Enum):
    """Status of a selection."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPORTED = "exported"


class SelectionPurpose(str, Enum):
    """Purpose/intent of a selection."""
    CURATION = "curation"          # General curation
    PRESENTATION = "presentation"  # For client presentation
    EXPORT = "export"             # For export/delivery
    REFERENCE = "reference"       # Style or mood reference
    TRAINING = "training"         # For model training
    PORTFOLIO = "portfolio"       # Portfolio pieces
    SOCIAL_MEDIA = "social_media" # Social media posts
    CUSTOM = "custom"             # Custom purpose


@dataclass
class SelectionItem:
    """An item in a selection with metadata."""

    # Core identifiers
    asset_hash: str               # Content hash of the asset
    file_path: str                # Current file path

    # Selection metadata
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    added_by: str = "alice"       # Who added it (alice, user, etc.)

    # Selection reasoning
    selection_reason: str | None = None      # Why this was selected
    quality_notes: str | None = None         # Quality observations
    usage_notes: str | None = None           # Intended usage notes

    # Categorization within selection
    tags: list[str] = field(default_factory=list)      # Additional tags for this selection
    role: str | None = None                          # Role in this selection (hero, supporting, etc.)
    sequence_order: int | None = None                # Order in sequence (if applicable)

    # Related assets
    related_assets: list[str] = field(default_factory=list)  # Other related asset hashes
    alternatives: list[str] = field(default_factory=list)    # Alternative options considered

    # Custom metadata
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "asset_hash": self.asset_hash,
            "file_path": self.file_path,
            "added_at": self.added_at.isoformat(),
            "added_by": self.added_by,
            "selection_reason": self.selection_reason,
            "quality_notes": self.quality_notes,
            "usage_notes": self.usage_notes,
            "tags": self.tags,
            "role": self.role,
            "sequence_order": self.sequence_order,
            "related_assets": self.related_assets,
            "alternatives": self.alternatives,
            "custom_metadata": self.custom_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectionItem":
        """Create from dictionary."""
        # Handle datetime conversion
        if isinstance(data.get("added_at"), str):
            if data is not None:
                data["added_at"] = datetime.fromisoformat(data["added_at"])
        return cls(**data)


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class SelectionHistory:
# TODO: Review unreachable code - """History entry for selection changes."""

# TODO: Review unreachable code - timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
# TODO: Review unreachable code - action: str = ""              # added, removed, updated, exported, etc.
# TODO: Review unreachable code - actor: str = "alice"          # Who made the change

# TODO: Review unreachable code - # What changed
# TODO: Review unreachable code - asset_hashes: list[str] = field(default_factory=list)  # Assets affected
# TODO: Review unreachable code - changes: dict[str, Any] = field(default_factory=dict)  # What changed
# TODO: Review unreachable code - notes: str | None = None                             # Human notes about the change

# TODO: Review unreachable code - def to_dict(self) -> dict[str, Any]:
# TODO: Review unreachable code - """Convert to dictionary for serialization."""
# TODO: Review unreachable code - return {
# TODO: Review unreachable code - "timestamp": self.timestamp.isoformat(),
# TODO: Review unreachable code - "action": self.action,
# TODO: Review unreachable code - "actor": self.actor,
# TODO: Review unreachable code - "asset_hashes": self.asset_hashes,
# TODO: Review unreachable code - "changes": self.changes,
# TODO: Review unreachable code - "notes": self.notes,
# TODO: Review unreachable code - }

# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def from_dict(cls, data: dict[str, Any]) -> "SelectionHistory":
# TODO: Review unreachable code - """Create from dictionary."""
# TODO: Review unreachable code - if isinstance(data.get("timestamp"), str):
# TODO: Review unreachable code - data["timestamp"] = datetime.fromisoformat(data["timestamp"])
# TODO: Review unreachable code - return cls(**data)


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class Selection:
# TODO: Review unreachable code - """A selection of assets for a specific purpose."""

# TODO: Review unreachable code - # Identifiers
# TODO: Review unreachable code - id: str = ""  # Will be set based on content hash or timestamp
# TODO: Review unreachable code - project_id: str = ""          # Associated project
# TODO: Review unreachable code - name: str = ""                # Human-readable name

# TODO: Review unreachable code - # Metadata
# TODO: Review unreachable code - created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
# TODO: Review unreachable code - updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
# TODO: Review unreachable code - created_by: str = "alice"     # Who created it

# TODO: Review unreachable code - # Selection details
# TODO: Review unreachable code - purpose: SelectionPurpose = SelectionPurpose.CURATION
# TODO: Review unreachable code - status: SelectionStatus = SelectionStatus.DRAFT
# TODO: Review unreachable code - description: str | None = None

# TODO: Review unreachable code - # Selection criteria
# TODO: Review unreachable code - criteria: dict[str, Any] = field(default_factory=dict)  # What criteria were used
# TODO: Review unreachable code - constraints: dict[str, Any] = field(default_factory=dict)  # Any constraints (max items, etc.)

# TODO: Review unreachable code - # Items in the selection
# TODO: Review unreachable code - items: list[SelectionItem] = field(default_factory=list)

# TODO: Review unreachable code - # Organization
# TODO: Review unreachable code - groups: dict[str, list[str]] = field(default_factory=dict)  # Group name -> asset hashes
# TODO: Review unreachable code - sequence: list[str] = field(default_factory=list)           # Ordered sequence of asset hashes

# TODO: Review unreachable code - # History
# TODO: Review unreachable code - history: list[SelectionHistory] = field(default_factory=list)

# TODO: Review unreachable code - # Export/delivery info
# TODO: Review unreachable code - export_settings: dict[str, Any] = field(default_factory=dict)
# TODO: Review unreachable code - export_history: list[dict[str, Any]] = field(default_factory=list)

# TODO: Review unreachable code - # Custom metadata
# TODO: Review unreachable code - tags: list[str] = field(default_factory=list)
# TODO: Review unreachable code - metadata: dict[str, Any] = field(default_factory=dict)

# TODO: Review unreachable code - def __post_init__(self):
# TODO: Review unreachable code - """Generate ID if not provided."""
# TODO: Review unreachable code - if not self.id:
# TODO: Review unreachable code - # Generate ID from project_id + name + timestamp
# TODO: Review unreachable code - # This makes it unique but reproducible for the same selection
# TODO: Review unreachable code - id_source = f"{self.project_id}:{self.name}:{self.created_at.isoformat()}"
# TODO: Review unreachable code - self.id = hashlib.sha256(id_source.encode()).hexdigest()[:16]

# TODO: Review unreachable code - def add_item(self, item: SelectionItem, notes: str | None = None) -> None:
# TODO: Review unreachable code - """Add an item to the selection."""
# TODO: Review unreachable code - self.items.append(item)
# TODO: Review unreachable code - self.updated_at = datetime.now(UTC)

# TODO: Review unreachable code - # Add history entry
# TODO: Review unreachable code - self.history.append(SelectionHistory(
# TODO: Review unreachable code - action="added",
# TODO: Review unreachable code - asset_hashes=[item.asset_hash],
# TODO: Review unreachable code - notes=notes
# TODO: Review unreachable code - ))

# TODO: Review unreachable code - def remove_item(self, asset_hash: str, reason: str | None = None) -> bool:
# TODO: Review unreachable code - """Remove an item from the selection."""
# TODO: Review unreachable code - for i, item in enumerate(self.items):
# TODO: Review unreachable code - if item.asset_hash == asset_hash:
# TODO: Review unreachable code - self.items.pop(i)
# TODO: Review unreachable code - self.updated_at = datetime.now(UTC)

# TODO: Review unreachable code - # Add history entry
# TODO: Review unreachable code - self.history.append(SelectionHistory(
# TODO: Review unreachable code - action="removed",
# TODO: Review unreachable code - asset_hashes=[asset_hash],
# TODO: Review unreachable code - notes=reason
# TODO: Review unreachable code - ))

# TODO: Review unreachable code - # Remove from groups and sequence
# TODO: Review unreachable code - for group_items in self.groups.values():
# TODO: Review unreachable code - if asset_hash in group_items:
# TODO: Review unreachable code - group_items.remove(asset_hash)
# TODO: Review unreachable code - if asset_hash in self.sequence:
# TODO: Review unreachable code - self.sequence.remove(asset_hash)

# TODO: Review unreachable code - return True
# TODO: Review unreachable code - return False

# TODO: Review unreachable code - def update_item(self, asset_hash: str, updates: dict[str, Any]) -> bool:
# TODO: Review unreachable code - """Update an item in the selection."""
# TODO: Review unreachable code - for item in self.items:
# TODO: Review unreachable code - if item.asset_hash == asset_hash:
# TODO: Review unreachable code - # Update fields
# TODO: Review unreachable code - for key, value in updates.items():
# TODO: Review unreachable code - if hasattr(item, key):
# TODO: Review unreachable code - setattr(item, key, value)

# TODO: Review unreachable code - self.updated_at = datetime.now(UTC)

# TODO: Review unreachable code - # Add history entry
# TODO: Review unreachable code - self.history.append(SelectionHistory(
# TODO: Review unreachable code - action="updated",
# TODO: Review unreachable code - asset_hashes=[asset_hash],
# TODO: Review unreachable code - changes=updates
# TODO: Review unreachable code - ))
# TODO: Review unreachable code - return True
# TODO: Review unreachable code - return False

# TODO: Review unreachable code - def get_item(self, asset_hash: str) -> SelectionItem | None:
# TODO: Review unreachable code - """Get an item by asset hash."""
# TODO: Review unreachable code - for item in self.items:
# TODO: Review unreachable code - if item.asset_hash == asset_hash:
# TODO: Review unreachable code - return item
# TODO: Review unreachable code - return None

# TODO: Review unreachable code - def get_asset_hashes(self) -> set[str]:
# TODO: Review unreachable code - """Get all asset hashes in the selection."""
# TODO: Review unreachable code - return {item.asset_hash for item in self.items}

# TODO: Review unreachable code - def group_items(self, group_name: str, asset_hashes: list[str]) -> None:
# TODO: Review unreachable code - """Group items together."""
# TODO: Review unreachable code - valid_hashes = [h for h in asset_hashes if h in self.get_asset_hashes()]
# TODO: Review unreachable code - if valid_hashes:
# TODO: Review unreachable code - self.groups[group_name] = valid_hashes
# TODO: Review unreachable code - self.updated_at = datetime.now(UTC)

# TODO: Review unreachable code - # Add history entry
# TODO: Review unreachable code - self.history.append(SelectionHistory(
# TODO: Review unreachable code - action="grouped",
# TODO: Review unreachable code - asset_hashes=valid_hashes,
# TODO: Review unreachable code - changes={"group": group_name}
# TODO: Review unreachable code - ))

# TODO: Review unreachable code - def set_sequence(self, asset_hashes: list[str]) -> None:
# TODO: Review unreachable code - """Set the sequence order of assets."""
# TODO: Review unreachable code - valid_hashes = [h for h in asset_hashes if h in self.get_asset_hashes()]
# TODO: Review unreachable code - self.sequence = valid_hashes
# TODO: Review unreachable code - self.updated_at = datetime.now(UTC)

# TODO: Review unreachable code - # Update sequence_order in items
# TODO: Review unreachable code - for i, hash in enumerate(valid_hashes):
# TODO: Review unreachable code - item = self.get_item(hash)
# TODO: Review unreachable code - if item:
# TODO: Review unreachable code - item.sequence_order = i

# TODO: Review unreachable code - # Add history entry
# TODO: Review unreachable code - self.history.append(SelectionHistory(
# TODO: Review unreachable code - action="sequenced",
# TODO: Review unreachable code - asset_hashes=valid_hashes,
# TODO: Review unreachable code - changes={"sequence": valid_hashes}
# TODO: Review unreachable code - ))

# TODO: Review unreachable code - def to_dict(self) -> dict[str, Any]:
# TODO: Review unreachable code - """Convert to dictionary for serialization."""
# TODO: Review unreachable code - return {
# TODO: Review unreachable code - "id": self.id,
# TODO: Review unreachable code - "project_id": self.project_id,
# TODO: Review unreachable code - "name": self.name,
# TODO: Review unreachable code - "created_at": self.created_at.isoformat(),
# TODO: Review unreachable code - "updated_at": self.updated_at.isoformat(),
# TODO: Review unreachable code - "created_by": self.created_by,
# TODO: Review unreachable code - "purpose": self.purpose.value,
# TODO: Review unreachable code - "status": self.status.value,
# TODO: Review unreachable code - "description": self.description,
# TODO: Review unreachable code - "criteria": self.criteria,
# TODO: Review unreachable code - "constraints": self.constraints,
# TODO: Review unreachable code - "items": [item.to_dict() for item in self.items],
# TODO: Review unreachable code - "groups": self.groups,
# TODO: Review unreachable code - "sequence": self.sequence,
# TODO: Review unreachable code - "history": [h.to_dict() for h in self.history],
# TODO: Review unreachable code - "export_settings": self.export_settings,
# TODO: Review unreachable code - "export_history": self.export_history,
# TODO: Review unreachable code - "tags": self.tags,
# TODO: Review unreachable code - "metadata": self.metadata,
# TODO: Review unreachable code - }

# TODO: Review unreachable code - @classmethod
# TODO: Review unreachable code - def from_dict(cls, data: dict[str, Any]) -> "Selection":
# TODO: Review unreachable code - """Create from dictionary."""
# TODO: Review unreachable code - # Convert enums
# TODO: Review unreachable code - if isinstance(data.get("purpose"), str):
# TODO: Review unreachable code - data["purpose"] = SelectionPurpose(data["purpose"])
# TODO: Review unreachable code - if isinstance(data.get("status"), str):
# TODO: Review unreachable code - data["status"] = SelectionStatus(data["status"])

# TODO: Review unreachable code - # Convert dates
# TODO: Review unreachable code - if isinstance(data.get("created_at"), str):
# TODO: Review unreachable code - data["created_at"] = datetime.fromisoformat(data["created_at"])
# TODO: Review unreachable code - if isinstance(data.get("updated_at"), str):
# TODO: Review unreachable code - data["updated_at"] = datetime.fromisoformat(data["updated_at"])

# TODO: Review unreachable code - # Convert items
# TODO: Review unreachable code - if data is not None and "items" in data:
# TODO: Review unreachable code - data["items"] = [SelectionItem.from_dict(item) for item in data["items"]]

# TODO: Review unreachable code - # Convert history
# TODO: Review unreachable code - if data is not None and "history" in data:
# TODO: Review unreachable code - data["history"] = [SelectionHistory.from_dict(h) for h in data["history"]]

# TODO: Review unreachable code - return cls(**data)
