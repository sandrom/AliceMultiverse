"""Type definitions for AliceMultiverse."""

from typing import TypedDict, Optional, Dict, List, Any, Literal, Union
from pathlib import Path
from datetime import datetime
from enum import Enum


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
    file_number: Optional[int]
    quality_stars: Optional[int]
    brisque_score: Optional[float]
    pipeline_result: Optional[str]


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
    destination: Optional[str]
    date: Optional[str]
    source_type: Optional[str]
    media_type: Optional[MediaType]
    file_number: Optional[int]
    quality_stars: Optional[int]
    brisque_score: Optional[float]
    pipeline_result: Optional[str]
    error: Optional[str]


class Statistics(TypedDict):
    """Organization statistics."""
    total: int
    organized: int
    already_organized: int
    duplicates: int
    errors: int
    moved_existing: int
    by_date: Dict[str, int]
    by_source: Dict[str, int]
    by_project: Dict[str, int]
    by_quality: Dict[int, int]
    quality_assessed: int
    quality_skipped: int
    images_found: int
    videos_found: int
    pipeline_results: Dict[str, int]
    pipeline_costs: Dict[str, float]