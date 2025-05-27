"""Request and response models for Alice interface."""

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

    # Filters
    source_types: list[str] | None  # ["midjourney", "flux"]
    min_quality_stars: int | None
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
    quality_assessment: bool | None
    pipeline: str | None
    watch_mode: bool | None


class TagRequest(TypedDict):
    """Request to tag assets."""

    asset_ids: list[str]
    style_tags: list[str] | None
    mood_tags: list[str] | None
    subject_tags: list[str] | None
    custom_tags: list[str] | None
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
