"""Models for selection tracking system."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


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
    added_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    added_by: str = "alice"       # Who added it (alice, user, etc.)
    
    # Selection reasoning
    selection_reason: Optional[str] = None      # Why this was selected
    quality_notes: Optional[str] = None         # Quality observations
    usage_notes: Optional[str] = None           # Intended usage notes
    
    # Categorization within selection
    tags: List[str] = field(default_factory=list)      # Additional tags for this selection
    role: Optional[str] = None                          # Role in this selection (hero, supporting, etc.)
    sequence_order: Optional[int] = None                # Order in sequence (if applicable)
    
    # Related assets
    related_assets: List[str] = field(default_factory=list)  # Other related asset hashes
    alternatives: List[str] = field(default_factory=list)    # Alternative options considered
    
    # Custom metadata
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
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
    def from_dict(cls, data: Dict[str, Any]) -> "SelectionItem":
        """Create from dictionary."""
        # Handle datetime conversion
        if isinstance(data.get("added_at"), str):
            data["added_at"] = datetime.fromisoformat(data["added_at"])
        return cls(**data)


@dataclass
class SelectionHistory:
    """History entry for selection changes."""
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    action: str = ""              # added, removed, updated, exported, etc.
    actor: str = "alice"          # Who made the change
    
    # What changed
    asset_hashes: List[str] = field(default_factory=list)  # Assets affected
    changes: Dict[str, Any] = field(default_factory=dict)  # What changed
    notes: Optional[str] = None                             # Human notes about the change
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "actor": self.actor,
            "asset_hashes": self.asset_hashes,
            "changes": self.changes,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SelectionHistory":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class Selection:
    """A selection of assets for a specific purpose."""
    
    # Identifiers
    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str = ""          # Associated project
    name: str = ""                # Human-readable name
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "alice"     # Who created it
    
    # Selection details
    purpose: SelectionPurpose = SelectionPurpose.CURATION
    status: SelectionStatus = SelectionStatus.DRAFT
    description: Optional[str] = None
    
    # Selection criteria
    criteria: Dict[str, Any] = field(default_factory=dict)  # What criteria were used
    constraints: Dict[str, Any] = field(default_factory=dict)  # Any constraints (max items, etc.)
    
    # Items in the selection
    items: List[SelectionItem] = field(default_factory=list)
    
    # Organization
    groups: Dict[str, List[str]] = field(default_factory=dict)  # Group name -> asset hashes
    sequence: List[str] = field(default_factory=list)           # Ordered sequence of asset hashes
    
    # History
    history: List[SelectionHistory] = field(default_factory=list)
    
    # Export/delivery info
    export_settings: Dict[str, Any] = field(default_factory=dict)
    export_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Custom metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_item(self, item: SelectionItem, notes: Optional[str] = None) -> None:
        """Add an item to the selection."""
        self.items.append(item)
        self.updated_at = datetime.now(timezone.utc)
        
        # Add history entry
        self.history.append(SelectionHistory(
            action="added",
            asset_hashes=[item.asset_hash],
            notes=notes
        ))
    
    def remove_item(self, asset_hash: str, reason: Optional[str] = None) -> bool:
        """Remove an item from the selection."""
        for i, item in enumerate(self.items):
            if item.asset_hash == asset_hash:
                self.items.pop(i)
                self.updated_at = datetime.now(timezone.utc)
                
                # Add history entry
                self.history.append(SelectionHistory(
                    action="removed",
                    asset_hashes=[asset_hash],
                    notes=reason
                ))
                
                # Remove from groups and sequence
                for group_items in self.groups.values():
                    if asset_hash in group_items:
                        group_items.remove(asset_hash)
                if asset_hash in self.sequence:
                    self.sequence.remove(asset_hash)
                
                return True
        return False
    
    def update_item(self, asset_hash: str, updates: Dict[str, Any]) -> bool:
        """Update an item in the selection."""
        for item in self.items:
            if item.asset_hash == asset_hash:
                # Update fields
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                
                self.updated_at = datetime.now(timezone.utc)
                
                # Add history entry
                self.history.append(SelectionHistory(
                    action="updated",
                    asset_hashes=[asset_hash],
                    changes=updates
                ))
                return True
        return False
    
    def get_item(self, asset_hash: str) -> Optional[SelectionItem]:
        """Get an item by asset hash."""
        for item in self.items:
            if item.asset_hash == asset_hash:
                return item
        return None
    
    def get_asset_hashes(self) -> Set[str]:
        """Get all asset hashes in the selection."""
        return {item.asset_hash for item in self.items}
    
    def group_items(self, group_name: str, asset_hashes: List[str]) -> None:
        """Group items together."""
        valid_hashes = [h for h in asset_hashes if h in self.get_asset_hashes()]
        if valid_hashes:
            self.groups[group_name] = valid_hashes
            self.updated_at = datetime.now(timezone.utc)
            
            # Add history entry
            self.history.append(SelectionHistory(
                action="grouped",
                asset_hashes=valid_hashes,
                changes={"group": group_name}
            ))
    
    def set_sequence(self, asset_hashes: List[str]) -> None:
        """Set the sequence order of assets."""
        valid_hashes = [h for h in asset_hashes if h in self.get_asset_hashes()]
        self.sequence = valid_hashes
        self.updated_at = datetime.now(timezone.utc)
        
        # Update sequence_order in items
        for i, hash in enumerate(valid_hashes):
            item = self.get_item(hash)
            if item:
                item.sequence_order = i
        
        # Add history entry
        self.history.append(SelectionHistory(
            action="sequenced",
            asset_hashes=valid_hashes,
            changes={"sequence": valid_hashes}
        ))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "purpose": self.purpose.value,
            "status": self.status.value,
            "description": self.description,
            "criteria": self.criteria,
            "constraints": self.constraints,
            "items": [item.to_dict() for item in self.items],
            "groups": self.groups,
            "sequence": self.sequence,
            "history": [h.to_dict() for h in self.history],
            "export_settings": self.export_settings,
            "export_history": self.export_history,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Selection":
        """Create from dictionary."""
        # Convert enums
        if isinstance(data.get("purpose"), str):
            data["purpose"] = SelectionPurpose(data["purpose"])
        if isinstance(data.get("status"), str):
            data["status"] = SelectionStatus(data["status"])
        
        # Convert dates
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Convert items
        if "items" in data:
            data["items"] = [SelectionItem.from_dict(item) for item in data["items"]]
        
        # Convert history
        if "history" in data:
            data["history"] = [SelectionHistory.from_dict(h) for h in data["history"]]
        
        return cls(**data)