"""Type definitions for AliceMultiverse."""

from enum import Enum
from typing import Literal, TypedDict


class MediaType(Enum):
    """Type of media file."""

    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    UNKNOWN = "unknown"


# QualityRating removed - use understanding system instead


class AnalysisResult(TypedDict):
    """Result of media file analysis."""

    source_type: str
    date_taken: str
    project_folder: str
    media_type: MediaType
    file_number: int | None
    # Quality assessment moved to understanding system


class CacheMetadata(TypedDict):
    """Metadata stored in cache."""

    version: str
    file_hash: str
    content_hash: str
    original_path: str
    file_name: str
    file_size: int
    last_modified: float
    analysis: AnalysisResult
    analysis_time: float
    cached_at: str


class OrganizeResult(TypedDict):
    """Result of organizing a single media file."""

    source: str
    project_folder: str
    status: Literal["success", "duplicate", "error", "dry_run", "pending", "moved_existing"]
    destination: str | None
    date: str | None
    source_type: str | None
    media_type: MediaType | None
    file_number: int | None
    # Quality assessment moved to understanding system
    error: str | None


class Statistics(TypedDict):
    """Organization statistics."""

    total: int
    organized: int
    already_organized: int
    duplicates: int
    errors: int
    moved_existing: int
    by_date: dict[str, int]
    by_source: dict[str, int]
    by_project: dict[str, int]
    # Quality metrics moved to understanding system
    images_found: int
    videos_found: int
    # Pipeline results moved to understanding system
