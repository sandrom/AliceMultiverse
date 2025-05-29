"""Creative domain events for AliceMultiverse (v2).

These events represent creative decisions and context updates that enable
AI assistants to maintain continuity across sessions and understand the
creative chaos of each user.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base_v2 import BaseEvent


@dataclass
class ProjectCreatedEvent(BaseEvent):
    """Fired when a new creative project is created."""
    
    # Project identification
    project_id: str
    project_name: str
    
    # Project metadata
    description: Optional[str] = None
    project_type: Optional[str] = None  # 'music_video', 'art_series', 'story'
    
    # Creative context
    initial_context: Dict[str, Any] = field(default_factory=dict)
    style_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Creation context
    created_by: str = ""  # 'user', 'ai_assistant'
    parent_project_id: Optional[str] = None  # For project variations
    
    @property
    def event_type(self) -> str:
        return "project.created"


@dataclass
class StyleChosenEvent(BaseEvent):
    """Fired when a style decision is made for a project or asset."""
    
    # Context
    project_id: str
    
    # Style information
    style_name: str
    style_category: str  # 'visual', 'mood', 'technique', 'reference'
    
    # Optional context
    asset_id: Optional[str] = None  # Content hash if for specific asset
    
    # Style details
    style_parameters: Dict[str, Any] = field(default_factory=dict)
    reference_assets: List[str] = field(default_factory=list)  # Content hashes
    style_prompt: Optional[str] = None
    
    # Decision context
    chosen_by: str = ""  # 'user', 'ai_assistant'
    reason: Optional[str] = None
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def event_type(self) -> str:
        return "style.chosen"


@dataclass
class ContextUpdatedEvent(BaseEvent):
    """Fired when project creative context is updated.
    
    This is crucial for AI assistants to understand the evolution of
    creative projects and maintain continuity across sessions.
    """
    
    # Context identification
    project_id: str
    context_type: str  # 'character', 'narrative', 'visual', 'technical'
    
    # Update details
    update_type: str  # 'addition', 'modification', 'removal'
    context_key: str  # Specific aspect updated
    
    # Context data
    new_value: Dict[str, Any] = field(default_factory=dict)
    previous_value: Optional[Dict[str, Any]] = None
    
    # Metadata
    updated_by: str = ""  # 'user', 'ai_assistant', 'system'
    update_reason: Optional[str] = None
    related_assets: List[str] = field(default_factory=list)  # Content hashes
    
    # AI-relevant context
    natural_language_description: Optional[str] = None  # For AI understanding
    impacts: List[str] = field(default_factory=list)  # What this change affects
    
    @property
    def event_type(self) -> str:
        return "context.updated"


@dataclass
class CharacterDefinedEvent(BaseEvent):
    """Fired when a character is defined or updated in a project."""
    
    # Context
    project_id: str
    character_id: str
    
    # Character information
    character_name: str
    character_type: str  # 'protagonist', 'supporting', 'background'
    
    # Character details
    visual_description: Dict[str, Any] = field(default_factory=dict)
    personality_traits: List[str] = field(default_factory=list)
    backstory: Optional[str] = None
    
    # Visual references
    reference_assets: List[str] = field(default_factory=list)  # Content hashes
    style_guidelines: Dict[str, Any] = field(default_factory=dict)
    
    # Evolution tracking
    version: int = 1
    previous_version_id: Optional[str] = None
    changes_from_previous: List[str] = field(default_factory=list)
    
    @property
    def event_type(self) -> str:
        return "character.defined"


@dataclass
class ConceptApprovedEvent(BaseEvent):
    """Fired when a creative concept is approved for production."""
    
    # Context
    project_id: str
    concept_id: str
    
    # Concept details
    concept_type: str  # 'scene', 'sequence', 'overall'
    concept_name: str
    description: str
    
    # Approval details
    approved_by: str  # 'user', 'ai_assistant'
    
    # Optional details
    approval_notes: Optional[str] = None
    
    # Related assets
    concept_assets: List[str] = field(default_factory=list)  # Content hashes
    reference_materials: List[str] = field(default_factory=list)
    
    # Production readiness
    production_notes: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    @property
    def event_type(self) -> str:
        return "concept.approved"