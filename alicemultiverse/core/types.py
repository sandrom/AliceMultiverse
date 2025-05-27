"""Type definitions for AliceMultiverse."""

from enum import Enum
from typing import Literal, TypedDict


class MediaType(Enum):
    """Type of media file."""

    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    UNKNOWN = "unknown"


class QualityRating(Enum):
    """Quality rating levels."""

    FIVE_STAR = 5
    FOUR_STAR = 4
    THREE_STAR = 3
    TWO_STAR = 2
    ONE_STAR = 1
    UNRATED = 0


class AnalysisResult(TypedDict):
    """Result of media file analysis."""

    source_type: str
    date_taken: str
    project_folder: str
    media_type: MediaType
    file_number: int | None
    quality_stars: int | None
    brisque_score: float | None
    pipeline_result: str | None


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
    quality_stars: int | None
    brisque_score: float | None
    pipeline_result: str | None
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
    by_quality: dict[int, int]
    quality_assessed: int
    quality_skipped: int
    images_found: int
    videos_found: int
    pipeline_results: dict[str, int]
    pipeline_costs: dict[str, float]
