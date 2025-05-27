"""Structured request and response models for Alice interface following the API specification."""

from enum import Enum
from typing import Any, Literal, TypedDict


class MediaType(str, Enum):
    """Technical classification of media files."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class SortField(str, Enum):
    """Available sort fields for search results."""
    CREATED_DATE = "created_date"
    MODIFIED_DATE = "modified_date"
    QUALITY_RATING = "quality_rating"
    FILE_SIZE = "file_size"
    FILENAME = "filename"


class SortOrder(str, Enum):
    """Sort order direction."""
    ASC = "asc"
    DESC = "desc"


class AssetRole(str, Enum):
    """Creative role of an asset."""
    HERO = "hero"
    B_ROLL = "b_roll"
    REFERENCE = "reference"
    WIP = "wip"
    FINAL = "final"
    REJECTED = "rejected"


class RangeFilter(TypedDict, total=False):
    """Numeric range filter."""
    min: float | None
    max: float | None


class DimensionFilter(TypedDict, total=False):
    """Image/video dimension filters."""
    width: RangeFilter | None
    height: RangeFilter | None
    aspect_ratio: RangeFilter | None


class DateRange(TypedDict, total=False):
    """Date range filter."""
    start: str | None  # ISO 8601 date
    end: str | None    # ISO 8601 date


class SearchFilters(TypedDict, total=False):
    """Structured search filters matching the API specification."""

    # Technical filters
    media_type: MediaType | None
    file_formats: list[str] | None
    file_size: RangeFilter | None
    dimensions: DimensionFilter | None
    quality_rating: RangeFilter | None

    # Semantic filters (current: simple tags)
    tags: list[str] | None          # AND operation
    any_tags: list[str] | None      # OR operation
    exclude_tags: list[str] | None  # NOT operation

    # Future: tag:value pairs
    tag_values: dict[str, str | list[str]] | None
    tag_ranges: dict[str, RangeFilter] | None
    tag_patterns: dict[str, str] | None

    # Metadata filters
    ai_source: list[str] | None
    project: str | None
    content_hash: str | None
    has_metadata: list[str] | None

    # Temporal filters
    date_range: DateRange | None

    # Text search (structured)
    filename_pattern: str | None  # Regex pattern
    prompt_keywords: list[str] | None  # Keywords in prompt


class SearchRequest(TypedDict):
    """Structured search request following API specification."""
    filters: SearchFilters
    sort_by: SortField | None
    order: SortOrder | None
    limit: int | None  # Default: 50, Max: 1000
    offset: int | None  # Default: 0


class AssetMetadata(TypedDict, total=False):
    """Asset metadata structure."""
    dimensions: dict[str, int] | None
    prompt: str | None
    generation_params: dict[str, Any] | None
    # Allow arbitrary metadata
    # Note: In actual implementation, this would be more flexible


class Asset(TypedDict):
    """Asset information in search results."""
    content_hash: str
    file_path: str
    media_type: MediaType
    file_size: int

    # Metadata
    tags: list[str]
    ai_source: str | None
    quality_rating: float | None

    # Timestamps
    created_at: str
    modified_at: str
    discovered_at: str

    # Additional metadata
    metadata: AssetMetadata


class SearchFacet(TypedDict):
    """Individual facet with count."""
    value: str
    count: int


class SearchFacets(TypedDict, total=False):
    """Faceted search results for discovery."""
    tags: list[SearchFacet]
    ai_sources: list[SearchFacet]
    quality_ratings: list[SearchFacet]
    media_types: list[SearchFacet]


class SearchResponse(TypedDict):
    """Structured search response."""
    total_count: int
    results: list[Asset]
    facets: SearchFacets | None
    query_time_ms: int


class AliceResponse(TypedDict):
    """Standard response wrapper from Alice."""
    success: bool
    message: str
    data: Any
    error: str | None


# Additional structured requests for other operations

class OrganizeRequest(TypedDict, total=False):
    """Request to organize media files."""
    source_path: str | None
    destination_path: str | None
    organization_rules: dict[str, Any] | None
    quality_assessment: bool | None
    pipeline: str | None
    watch_mode: bool | None
    move_files: bool | None


class TagUpdateRequest(TypedDict):
    """Request to update asset tags."""
    asset_ids: list[str]
    add_tags: list[str] | None
    remove_tags: list[str] | None
    set_tags: list[str] | None  # Replace all tags


class GroupingRequest(TypedDict):
    """Request to group assets."""
    asset_ids: list[str]
    group_name: str
    group_metadata: dict[str, Any] | None


class ProjectRequest(TypedDict, total=False):
    """Request for project operations."""
    project_name: str
    filters: SearchFilters | None
    action: Literal["create", "update", "delete"] | None
    metadata: dict[str, Any] | None


class WorkflowRequest(TypedDict):
    """Request to execute a workflow."""
    workflow_name: str
    filters: SearchFilters
    parameters: dict[str, Any] | None
    dry_run: bool | None


class GenerationRequest(TypedDict, total=False):
    """Request for content generation (future)."""
    prompt: str
    model: str | None
    parameters: dict[str, Any] | None
    reference_assets: list[str] | None
    output_settings: dict[str, Any] | None
    project: str | None
    tags: list[str] | None
