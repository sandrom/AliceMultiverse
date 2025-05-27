"""Enhanced metadata models for AI-navigable asset management."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict


class AssetRole(Enum):
    """Creative role of an asset in a project."""

    HERO = "hero"  # Main/featured asset
    B_ROLL = "b_roll"  # Supporting footage
    REFERENCE = "reference"  # Style or concept reference
    TEST = "test"  # Test or experiment
    FINAL = "final"  # Final approved version
    WIP = "wip"  # Work in progress
    ARCHIVED = "archived"  # No longer active but kept


class AssetMetadata(TypedDict):
    """Complete metadata for an asset enabling AI navigation."""

    # Core identification
    asset_id: str  # Unique identifier (content hash)
    file_path: str  # Current file location
    file_name: str  # Original filename
    file_size: int  # Size in bytes
    mime_type: str  # MIME type

    # Temporal context
    created_at: datetime  # When asset was created
    modified_at: datetime  # Last modification
    imported_at: datetime  # When imported to Alice

    # Project context
    project_id: str  # Project this belongs to
    project_phase: str | None  # Phase when created (e.g., "concept", "production")
    session_id: str | None  # Work session identifier

    # Generation metadata
    source_type: str  # AI tool used (midjourney, flux, etc.)
    generation_params: dict[str, Any]  # Full generation parameters
    prompt: str | None  # Generation prompt if available
    model: str | None  # Specific model used
    seed: int | None  # Random seed if available

    # Semantic tags (AI-searchable)
    style_tags: list[str]  # Visual style (cyberpunk, minimalist, etc.)
    mood_tags: list[str]  # Mood/emotion (energetic, calm, dark)
    subject_tags: list[str]  # What's in it (portrait, landscape, object)
    color_tags: list[str]  # Dominant colors
    technical_tags: list[str]  # Technical aspects (high-contrast, shallow-dof)
    custom_tags: list[str]  # User-defined tags

    # Relationships
    parent_id: str | None  # If this is a variation/derivative
    variation_of: str | None  # Original if this is a variation
    similar_to: list[str]  # IDs of visually similar assets
    referenced_by: list[str]  # IDs of assets that reference this
    grouped_with: list[str]  # Logical grouping with other assets

    # Quality assessment
    quality_score: float | None  # Overall quality (0-100)
    quality_stars: int | None  # Star rating (1-5)
    technical_scores: dict[str, float]  # Detailed scores (sharpness, exposure, etc.)
    ai_defects: list[str]  # Detected AI artifacts

    # Creative metadata
    role: AssetRole  # Role in project
    description: str | None  # Human-readable description
    notes: str | None  # Creative notes
    approved: bool  # Approval status
    flagged: bool  # Flagged for review

    # Music video specific (optional)
    timecode: str | None  # Associated timecode
    beat_aligned: bool | None  # If aligned to beat
    scene_number: int | None  # Scene in video
    lyrics_line: str | None  # Associated lyrics


class ProjectContext(TypedDict):
    """Project-level context for AI understanding."""

    project_id: str
    name: str
    description: str | None
    created_at: datetime
    last_active: datetime

    # Creative direction
    style_guide: dict[str, Any]  # Visual style preferences
    color_palette: list[str]  # Project colors
    mood_board: list[str]  # Reference asset IDs
    inspiration_refs: list[str]  # External references

    # Project state
    current_phase: str  # concept, production, post, etc.
    completed_tasks: list[str]  # What's been done
    pending_tasks: list[str]  # What needs doing

    # Conversation history
    ai_interactions: list[dict]  # Previous AI conversations
    decisions_made: list[dict]  # Creative decisions

    # Statistics
    total_assets: int
    assets_by_role: dict[str, int]
    assets_by_phase: dict[str, int]
    favorite_styles: list[str]  # Most used styles


class SearchQuery(TypedDict):
    """Structure for asset search queries."""

    # Temporal filters
    timeframe_start: datetime | None
    timeframe_end: datetime | None
    created_in_phase: str | None

    # Tag-based search
    style_tags: list[str] | None
    mood_tags: list[str] | None
    subject_tags: list[str] | None
    any_tags: list[str] | None  # Match any of these
    all_tags: list[str] | None  # Must match all

    # Relationship search
    variations_of: str | None
    similar_to: str | None
    in_group: str | None

    # Quality filters
    min_quality_score: float | None
    min_stars: int | None
    exclude_defects: bool | None

    # Role/status filters
    roles: list[AssetRole] | None
    approved_only: bool | None
    exclude_archived: bool | None

    # Technical filters
    source_types: list[str] | None
    mime_types: list[str] | None

    # Sorting
    sort_by: Literal["created", "quality", "relevance"] | None
    limit: int | None


class AssetRelationship(TypedDict):
    """Defines relationships between assets."""

    from_asset: str
    to_asset: str
    relationship_type: Literal["parent", "variation", "reference", "similar", "grouped"]
    confidence: float | None  # For similarity relationships
    metadata: dict | None  # Additional relationship data


# Preset tag vocabularies for consistency
STYLE_VOCABULARY = {
    "cyberpunk",
    "minimalist",
    "baroque",
    "art-nouveau",
    "photorealistic",
    "anime",
    "watercolor",
    "oil-painting",
    "3d-render",
    "pixel-art",
    "abstract",
    "surreal",
    "vintage",
    "modern",
    "futuristic",
    "gothic",
    "impressionist",
    "pop-art",
    "grunge",
    "ethereal",
    "brutalist",
}

MOOD_VOCABULARY = {
    "energetic",
    "calm",
    "mysterious",
    "joyful",
    "melancholic",
    "dramatic",
    "peaceful",
    "intense",
    "playful",
    "serious",
    "romantic",
    "aggressive",
    "dreamy",
    "dark",
    "bright",
    "nostalgic",
    "hopeful",
    "ominous",
}

COLOR_VOCABULARY = {
    "red",
    "blue",
    "green",
    "yellow",
    "purple",
    "orange",
    "pink",
    "cyan",
    "magenta",
    "black",
    "white",
    "gray",
    "brown",
    "gold",
    "silver",
    "neon",
    "pastel",
    "monochrome",
    "vibrant",
    "muted",
    "warm",
    "cool",
}
