"""Request and response models for Alice interface."""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from datetime import datetime


class AliceResponse(TypedDict):
    """Standard response from Alice."""
    success: bool
    message: str
    data: Optional[Any]
    error: Optional[str]


class SearchRequest(TypedDict):
    """Request to search for assets."""
    # Natural language components
    description: Optional[str]  # "cyberpunk portraits with neon"
    time_reference: Optional[str]  # "last week", "yesterday", "October"
    
    # Structured search
    style_tags: Optional[List[str]]
    mood_tags: Optional[List[str]]
    subject_tags: Optional[List[str]]
    
    # Filters
    source_types: Optional[List[str]]  # ["midjourney", "flux"]
    min_quality_stars: Optional[int]
    roles: Optional[List[str]]  # ["hero", "b_roll"]
    
    # Options
    limit: Optional[int]
    sort_by: Optional[Literal["created", "quality", "relevance"]]


class GenerateRequest(TypedDict):
    """Request to generate new content."""
    prompt: str
    style_reference: Optional[str]  # Asset ID to use as style reference
    
    # Generation parameters
    model: Optional[str]  # If not specified, Alice chooses
    parameters: Optional[Dict[str, Any]]
    
    # Organization
    project_id: Optional[str]
    role: Optional[str]  # "hero", "b_roll", etc.
    tags: Optional[List[str]]


class OrganizeRequest(TypedDict):
    """Request to organize media files."""
    source_path: Optional[str]  # If not specified, uses default inbox
    enhanced_metadata: Optional[bool]
    quality_assessment: Optional[bool]
    pipeline: Optional[str]
    watch_mode: Optional[bool]


class TagRequest(TypedDict):
    """Request to tag assets."""
    asset_ids: List[str]
    style_tags: Optional[List[str]]
    mood_tags: Optional[List[str]]
    subject_tags: Optional[List[str]]
    custom_tags: Optional[List[str]]
    role: Optional[str]  # Asset role like "hero", "b_roll", etc.


class GroupRequest(TypedDict):
    """Request to group assets."""
    asset_ids: List[str]
    group_name: str
    group_type: Optional[str]  # For future expansion


class ProjectContextRequest(TypedDict):
    """Request for project context."""
    project_id: Optional[str]
    include_stats: Optional[bool]
    include_recent_assets: Optional[bool]


class AssetInfo(TypedDict):
    """Simplified asset information for AI."""
    id: str
    filename: str
    prompt: Optional[str]
    tags: List[str]
    quality_stars: Optional[int]
    role: str
    created: str  # ISO format
    source: str
    relationships: Dict[str, List[str]]  # type -> [asset_ids]