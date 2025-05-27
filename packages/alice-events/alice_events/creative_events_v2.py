"""Creative domain events for AliceMultiverse (v2).

These events represent creative decisions and context updates that enable
AI assistants to maintain continuity across sessions and understand the
creative chaos of each user.
"""

from dataclasses import dataclass, field
from typing import Any

from .base_v2 import BaseEvent


@dataclass
class ProjectCreatedEvent(BaseEvent):
    """Fired when a new creative project is created."""

    # Project identification
    project_id: str
    project_name: str

    # Project metadata
    description: str | None = None
    project_type: str | None = None  # 'music_video', 'art_series', 'story'

    # Creative context
    initial_context: dict[str, Any] = field(default_factory=dict)
    style_preferences: dict[str, Any] = field(default_factory=dict)

    # Creation context
    created_by: str = ""  # 'user', 'ai_assistant'
    parent_project_id: str | None = None  # For project variations

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
    asset_id: str | None = None  # Content hash if for specific asset

    # Style details
    style_parameters: dict[str, Any] = field(default_factory=dict)
    reference_assets: list[str] = field(default_factory=list)  # Content hashes
    style_prompt: str | None = None

    # Decision context
    chosen_by: str = ""  # 'user', 'ai_assistant'
    reason: str | None = None
    alternatives_considered: list[dict[str, Any]] = field(default_factory=list)

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
    new_value: dict[str, Any] = field(default_factory=dict)
    previous_value: dict[str, Any] | None = None

    # Metadata
    updated_by: str = ""  # 'user', 'ai_assistant', 'system'
    update_reason: str | None = None
    related_assets: list[str] = field(default_factory=list)  # Content hashes

    # AI-relevant context
    natural_language_description: str | None = None  # For AI understanding
    impacts: list[str] = field(default_factory=list)  # What this change affects

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
    visual_description: dict[str, Any] = field(default_factory=dict)
    personality_traits: list[str] = field(default_factory=list)
    backstory: str | None = None

    # Visual references
    reference_assets: list[str] = field(default_factory=list)  # Content hashes
    style_guidelines: dict[str, Any] = field(default_factory=dict)

    # Evolution tracking
    version: int = 1
    previous_version_id: str | None = None
    changes_from_previous: list[str] = field(default_factory=list)

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
    approval_notes: str | None = None

    # Related assets
    concept_assets: list[str] = field(default_factory=list)  # Content hashes
    reference_materials: list[str] = field(default_factory=list)

    # Production readiness
    production_notes: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "concept.approved"
