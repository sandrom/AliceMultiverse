"""Request and response models for Alice interface."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict


class AliceResponse(TypedDict):
    """Standard response from Alice."""

    success: bool
    message: str
    data: Any | None
    error: str | None


class SearchRequest(TypedDict):
    """Request to search for assets."""

    # Natural language components
    description: str | None  # "cyberpunk portraits with neon"
    time_reference: str | None  # "last week", "yesterday", "October"

    # Structured search
    style_tags: list[str] | None
    mood_tags: list[str] | None
    subject_tags: list[str] | None
    tag_mode: Literal["any", "all"] | None  # "any" for OR, "all" for AND

    # Filters
    source_types: list[str] | None  # ["midjourney", "flux"]
    # Quality filtering moved to understanding system
    roles: list[str] | None  # ["hero", "b_roll"]

    # Options
    limit: int | None
    sort_by: Literal["created", "quality", "relevance"] | None


class GenerateRequest(TypedDict):
    """Request to generate new content."""

    prompt: str
    style_reference: str | None  # Asset ID to use as style reference

    # Generation parameters
    model: str | None  # If not specified, Alice chooses
    parameters: dict[str, Any] | None

    # Organization
    project_id: str | None
    role: str | None  # "hero", "b_roll", etc.
    tags: list[str] | None


class OrganizeRequest(TypedDict):
    """Request to organize media files."""

    source_path: str | None  # If not specified, uses default inbox
    enhanced_metadata: bool | None
    quality_assessment: bool | None  # Deprecated - use understanding instead
    understanding: bool | None  # Enable AI-powered image understanding
    watch_mode: bool | None


class TagRequest(TypedDict):
    """Request to tag assets."""

    asset_ids: list[str]
    # Legacy format - individual tag lists
    style_tags: list[str] | None
    mood_tags: list[str] | None
    subject_tags: list[str] | None
    custom_tags: list[str] | None
    # New structured format - key:value pairs
    tags: list[str] | dict[str, list[str]] | None  # Either ["tag1", "tag2"] or {"style": ["cyberpunk"], "mood": ["dark"]}
    role: str | None  # Asset role like "hero", "b_roll", etc.


class GroupRequest(TypedDict):
    """Request to group assets."""

    asset_ids: list[str]
    group_name: str
    group_type: str | None  # For future expansion


class ProjectContextRequest(TypedDict):
    """Request for project context."""

    project_id: str | None
    include_stats: bool | None
    include_recent_assets: bool | None


class AssetInfo(TypedDict):
    """Simplified asset information for AI."""

    id: str
    filename: str
    prompt: str | None
    tags: list[str]
    quality_stars: int | None
    role: str
    created: str  # ISO format
    source: str
    relationships: dict[str, list[str]]  # type -> [asset_ids]


# New models for image presentation and browsing

@dataclass
class PresentableImage:
    """Image data optimized for chat display"""
    hash: str
    path: str
    thumbnail_url: str  # Base64 or file:// URL
    display_url: str    # Full resolution for detail view

    # Key metadata for display
    tags: list[str]
    source: str  # midjourney, dalle, etc.
    created_date: datetime

    # Understanding data
    description: str  # AI-generated description
    mood: list[str]
    style: list[str]
    colors: list[str]

    # Selection history
    previously_selected: bool = False
    selection_reason: str | None = None

    # Technical info
    dimensions: tuple[int, int] = (0, 0)
    file_size: int = 0

    def to_display_dict(self) -> dict[str, Any]:
        """Convert to dictionary for chat display"""
        return {
            "id": self.hash,
            "thumbnail": self.thumbnail_url,
            "display_url": self.display_url,
            "caption": self.description,
            "tags": self.tags,
            "source": self.source,
            "mood": self.mood,
            "style": self.style,
            "colors": self.colors,
            "selectable": True,
            "previously_selected": self.previously_selected,
            "selection_reason": self.selection_reason,
            "created": self.created_date.isoformat() if self.created_date else None
        }


@dataclass
class ImageSearchResult:
    """Results formatted for AI chat display"""
    images: list[PresentableImage]
    total_count: int
    has_more: bool
    query_interpretation: str  # How we understood the query
    suggestions: list[str]  # Suggested refinements

    def to_chat_response(self) -> dict[str, Any]:
        """Format for chat UI display"""
        return {
            "images": [img.to_display_dict() for img in self.images],
            "total": self.total_count,
            "has_more": self.has_more,
            "query_interpretation": self.query_interpretation,
            "instructions": "Click images to select. Tell me what you like/dislike.",
            "suggestions": self.suggestions
        }


@dataclass
class SelectionFeedback:
    """User feedback on image selection"""
    image_hash: str
    selected: bool
    reason: str | None = None
    session_id: str | None = None
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SoftDeleteCategory(str, Enum):
    """Categories for soft-deleted images"""
    REJECTED = "rejected"
    BROKEN = "broken"
    MAYBE_LATER = "maybe-later"
