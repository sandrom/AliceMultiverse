"""Enhanced metadata models for AI-navigable asset management."""

from typing import TypedDict, Optional, Dict, List, Any, Literal, Set
from datetime import datetime
from enum import Enum
from pathlib import Path


class AssetRole(Enum):
    """Creative role of an asset in a project."""
    HERO = "hero"          # Main/featured asset
    B_ROLL = "b_roll"      # Supporting footage
    REFERENCE = "reference" # Style or concept reference
    TEST = "test"          # Test or experiment
    FINAL = "final"        # Final approved version
    WIP = "wip"            # Work in progress
    ARCHIVED = "archived"  # No longer active but kept


class AssetMetadata(TypedDict):
    """Complete metadata for an asset enabling AI navigation."""
    # Core identification
    asset_id: str              # Unique identifier (content hash)
    file_path: str             # Current file location
    file_name: str             # Original filename
    file_size: int             # Size in bytes
    mime_type: str             # MIME type
    
    # Temporal context
    created_at: datetime       # When asset was created
    modified_at: datetime      # Last modification
    imported_at: datetime      # When imported to Alice
    
    # Project context
    project_id: str            # Project this belongs to
    project_phase: Optional[str]  # Phase when created (e.g., "concept", "production")
    session_id: Optional[str]     # Work session identifier
    
    # Generation metadata
    source_type: str           # AI tool used (midjourney, flux, etc.)
    generation_params: Dict[str, Any]  # Full generation parameters
    prompt: Optional[str]      # Generation prompt if available
    model: Optional[str]       # Specific model used
    seed: Optional[int]        # Random seed if available
    
    # Semantic tags (AI-searchable)
    style_tags: List[str]      # Visual style (cyberpunk, minimalist, etc.)
    mood_tags: List[str]       # Mood/emotion (energetic, calm, dark)
    subject_tags: List[str]    # What's in it (portrait, landscape, object)
    color_tags: List[str]      # Dominant colors
    technical_tags: List[str]  # Technical aspects (high-contrast, shallow-dof)
    custom_tags: List[str]     # User-defined tags
    
    # Relationships
    parent_id: Optional[str]   # If this is a variation/derivative
    variation_of: Optional[str] # Original if this is a variation
    similar_to: List[str]      # IDs of visually similar assets
    referenced_by: List[str]   # IDs of assets that reference this
    grouped_with: List[str]    # Logical grouping with other assets
    
    # Quality assessment
    quality_score: Optional[float]     # Overall quality (0-100)
    quality_stars: Optional[int]       # Star rating (1-5)
    technical_scores: Dict[str, float] # Detailed scores (sharpness, exposure, etc.)
    ai_defects: List[str]             # Detected AI artifacts
    
    # Creative metadata
    role: AssetRole           # Role in project
    description: Optional[str] # Human-readable description
    notes: Optional[str]      # Creative notes
    approved: bool            # Approval status
    flagged: bool            # Flagged for review
    
    # Music video specific (optional)
    timecode: Optional[str]   # Associated timecode
    beat_aligned: Optional[bool]  # If aligned to beat
    scene_number: Optional[int]   # Scene in video
    lyrics_line: Optional[str]    # Associated lyrics


class ProjectContext(TypedDict):
    """Project-level context for AI understanding."""
    project_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    last_active: datetime
    
    # Creative direction
    style_guide: Dict[str, Any]     # Visual style preferences
    color_palette: List[str]        # Project colors
    mood_board: List[str]           # Reference asset IDs
    inspiration_refs: List[str]     # External references
    
    # Project state
    current_phase: str              # concept, production, post, etc.
    completed_tasks: List[str]      # What's been done
    pending_tasks: List[str]        # What needs doing
    
    # Conversation history
    ai_interactions: List[Dict]     # Previous AI conversations
    decisions_made: List[Dict]      # Creative decisions
    
    # Statistics
    total_assets: int
    assets_by_role: Dict[str, int]
    assets_by_phase: Dict[str, int]
    favorite_styles: List[str]      # Most used styles


class SearchQuery(TypedDict):
    """Structure for asset search queries."""
    # Temporal filters
    timeframe_start: Optional[datetime]
    timeframe_end: Optional[datetime]
    created_in_phase: Optional[str]
    
    # Tag-based search
    style_tags: Optional[List[str]]
    mood_tags: Optional[List[str]]
    subject_tags: Optional[List[str]]
    any_tags: Optional[List[str]]      # Match any of these
    all_tags: Optional[List[str]]      # Must match all
    
    # Relationship search
    variations_of: Optional[str]
    similar_to: Optional[str]
    in_group: Optional[str]
    
    # Quality filters
    min_quality_score: Optional[float]
    min_stars: Optional[int]
    exclude_defects: Optional[bool]
    
    # Role/status filters
    roles: Optional[List[AssetRole]]
    approved_only: Optional[bool]
    exclude_archived: Optional[bool]
    
    # Technical filters
    source_types: Optional[List[str]]
    mime_types: Optional[List[str]]
    
    # Sorting
    sort_by: Optional[Literal["created", "quality", "relevance"]]
    limit: Optional[int]


class AssetRelationship(TypedDict):
    """Defines relationships between assets."""
    from_asset: str
    to_asset: str
    relationship_type: Literal["parent", "variation", "reference", "similar", "grouped"]
    confidence: Optional[float]  # For similarity relationships
    metadata: Optional[Dict]     # Additional relationship data


# Preset tag vocabularies for consistency
STYLE_VOCABULARY = {
    "cyberpunk", "minimalist", "baroque", "art-nouveau", "photorealistic",
    "anime", "watercolor", "oil-painting", "3d-render", "pixel-art",
    "abstract", "surreal", "vintage", "modern", "futuristic", "gothic",
    "impressionist", "pop-art", "grunge", "ethereal", "brutalist"
}

MOOD_VOCABULARY = {
    "energetic", "calm", "mysterious", "joyful", "melancholic", "dramatic",
    "peaceful", "intense", "playful", "serious", "romantic", "aggressive",
    "dreamy", "dark", "bright", "nostalgic", "hopeful", "ominous"
}

COLOR_VOCABULARY = {
    "red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan",
    "magenta", "black", "white", "gray", "brown", "gold", "silver",
    "neon", "pastel", "monochrome", "vibrant", "muted", "warm", "cool"
}