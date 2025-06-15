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


class SearchFilters(TypedDict, total=False):
    """All available search filters."""
    media_type: MediaType | None
    tags: list[str] | None
    any_tags: list[str] | None
    not_tags: list[str] | None
    quality_rating: RangeFilter | None
    ai_source: str | list[str] | None
    created_date: RangeFilter | None
    modified_date: RangeFilter | None
    file_size: RangeFilter | None
    dimensions: DimensionFilter | None
    file_formats: list[str] | None
    project: str | None
    group: str | None
    filename_pattern: str | None
    prompt_keywords: list[str] | None


class SearchFacet(TypedDict):
    """Facet count for search results."""
    value: str
    count: int


class SearchFacets(TypedDict, total=False):
    """Aggregated facets from search results."""
    tags: list[SearchFacet]
    ai_sources: list[SearchFacet]
    quality_ratings: list[SearchFacet]
    media_types: list[SearchFacet]
    projects: list[SearchFacet]
    groups: list[SearchFacet]


class Asset(TypedDict):
    """Asset information."""
    content_hash: str
    file_path: str
    media_type: MediaType
    file_size: int
    tags: list[str]
    ai_source: str | None
    quality_rating: int | None
    created_at: str
    modified_at: str
    discovered_at: str
    metadata: dict[str, Any]


class SearchRequest(TypedDict, total=False):
    """Search request parameters."""
    filters: SearchFilters | None
    sort_by: SortField | None
    order: SortOrder | None
    limit: int | None
    offset: int | None


class SearchResponse(TypedDict):
    """Search response with results and facets."""
    total_count: int
    results: list[Asset]
    facets: SearchFacets | None
    query_time_ms: int


class OrganizeRequest(TypedDict, total=False):
    """Request to organize media files."""
    source_path: str | None
    destination_path: str | None
    quality_assessment: bool | None  # Deprecated
    understanding: bool | None  # Enable AI understanding
    watch_mode: bool | None
    move_files: bool | None
    custom_rules: dict[str, Any] | None


class AssetInfo(TypedDict):
    """Basic asset information for responses."""
    content_hash: str
    file_path: str
    media_type: MediaType
    tags: list[str]


class AliceResponse(TypedDict):
    """Standard response format for all Alice operations."""
    success: bool
    message: str
    data: Any | None
    error: str | None


class BatchImagePresentationRequest(TypedDict):
    """Request to present multiple images for review."""
    asset_ids: list[str]
    session_id: str | None
    grid_size: str | None


class ImageSelectionFeedback(TypedDict):
    """Feedback on image selection."""
    asset_id: str
    selected: bool
    reason: str | None
    tags: list[str] | None


class BatchSelectionFeedback(TypedDict):
    """Batch feedback on multiple selections."""
    session_id: str
    selections: list[ImageSelectionFeedback]
    context: str | None


class TagUpdateRequest(TypedDict):
    """Request to update asset tags."""
    asset_ids: list[str]
    add_tags: list[str] | None
    remove_tags: list[str] | None
    set_tags: list[str] | None


class GroupingRequest(TypedDict):
    """Request to group assets together."""
    asset_ids: list[str]
    group_name: str
    group_metadata: dict[str, Any] | None


class ProjectRequest(TypedDict, total=False):
    """Request for project operations."""
    operation: Literal["create", "update", "list", "get", "delete"]
    project_id: str | None
    name: str | None
    metadata: dict[str, Any] | None


class WorkflowRequest(TypedDict):
    """Request to execute a workflow."""
    workflow_id: str
    input_assets: list[str]
    parameters: dict[str, Any] | None
    output_settings: dict[str, Any] | None


class GenerationRequest(TypedDict, total=False):
    """Request for content generation (future)."""
    prompt: str
    model: str | None
    parameters: dict[str, Any] | None
    reference_assets: list[str] | None
    output_settings: dict[str, Any] | None
    project: str | None
    tags: list[str] | None


class SoftDeleteRequest(TypedDict):
    """Request to soft delete assets."""
    asset_ids: list[str]
    category: Literal["broken", "duplicate", "maybe-later", "rejected", "archive"]
    reason: str | None


class SelectionPurpose(str, Enum):
    """Purpose of a selection."""
    CURATION = "curation"
    PRESENTATION = "presentation"
    EXPORT = "export"
    REFERENCE = "reference"
    TRAINING = "training"
    PORTFOLIO = "portfolio"
    SOCIAL_MEDIA = "social_media"
    CUSTOM = "custom"


class SelectionStatus(str, Enum):
    """Status of a selection."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPORTED = "exported"


class SelectionCreateRequest(TypedDict):
    """Request to create a new selection."""
    project_id: str
    name: str
    purpose: SelectionPurpose | None
    description: str | None
    criteria: dict[str, Any] | None
    constraints: dict[str, Any] | None
    tags: list[str] | None
    metadata: dict[str, Any] | None


class SelectionItemRequest(TypedDict):
    """Request to add/update selection items."""
    asset_hash: str
    file_path: str
    selection_reason: str | None
    quality_notes: str | None
    usage_notes: str | None
    tags: list[str] | None
    role: str | None
    related_assets: list[str] | None
    alternatives: list[str] | None
    custom_metadata: dict[str, Any] | None


class SelectionUpdateRequest(TypedDict, total=False):
    """Request to update selection items."""
    selection_id: str
    add_items: list[SelectionItemRequest] | None
    remove_items: list[str] | None  # asset hashes
    update_status: SelectionStatus | None
    update_metadata: dict[str, Any] | None
    notes: str | None


class SelectionExportRequest(TypedDict):
    """Request to export a selection."""
    selection_id: str
    export_path: str
    export_settings: dict[str, Any] | None


class SelectionSearchRequest(TypedDict, total=False):
    """Request to search for selections."""
    project_id: str
    status: SelectionStatus | None
    purpose: SelectionPurpose | None
    containing_asset: str | None  # Find selections containing this asset hash
