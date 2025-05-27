"""Asset-related events for AliceMultiverse - Version 2.

These events represent facts about asset lifecycle without inheritance issues.
"""

from dataclasses import dataclass, field
from typing import Any

from .base_v2 import BaseEvent


@dataclass
class AssetDiscoveredEvent(BaseEvent):
    """Fired when a new asset is discovered in the inbox."""

    # Required fields
    file_path: str
    content_hash: str
    file_size: int
    media_type: str  # 'image' or 'video'
    project_name: str

    # Optional fields
    source_type: str | None = None  # AI generator if detected
    inbox_path: str = ""
    discovery_source: str = "file_scan"  # 'file_scan', 'watch_mode', 'manual'

    @property
    def event_type(self) -> str:
        return "asset.discovered"


@dataclass
class AssetProcessedEvent(BaseEvent):
    """Fired when an asset has been processed (analyzed, metadata extracted)."""

    # Required fields
    content_hash: str
    file_path: str

    # Optional fields
    metadata: dict[str, Any] = field(default_factory=dict)
    extracted_metadata: dict[str, Any] = field(default_factory=dict)
    generation_params: dict[str, Any] = field(default_factory=dict)
    processing_duration_ms: int = 0
    processor_version: str = ""

    @property
    def event_type(self) -> str:
        return "asset.processed"


@dataclass
class AssetOrganizedEvent(BaseEvent):
    """Fired when an asset has been organized to its destination."""

    # Required fields
    content_hash: str
    source_path: str
    destination_path: str
    project_name: str
    source_type: str
    date_folder: str  # YYYY-MM-DD format

    # Optional fields
    quality_folder: str | None = None  # e.g., "5-star"
    operation: str = "copy"  # 'copy' or 'move'
    sequence_number: int | None = None

    @property
    def event_type(self) -> str:
        return "asset.organized"


@dataclass
class QualityAssessedEvent(BaseEvent):
    """Fired when quality assessment is completed for an asset."""

    # Required fields
    content_hash: str
    file_path: str
    star_rating: int  # 1-5 stars
    combined_score: float  # 0-1 normalized

    # Optional fields
    brisque_score: float | None = None
    sightengine_score: float | None = None
    claude_assessment: dict[str, Any] | None = None
    quality_issues: list[str] = field(default_factory=list)
    pipeline_mode: str = ""  # 'basic', 'standard', 'premium'
    assessment_duration_ms: int = 0
    stages_completed: list[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "quality.assessed"


@dataclass
class MetadataUpdatedEvent(BaseEvent):
    """Fired when asset metadata is updated."""

    # Required fields
    content_hash: str

    # Optional fields
    file_path: str | None = None
    metadata_type: str = ""  # 'embedded', 'cached', 'database'
    updated_fields: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    update_reason: str = ""  # 'quality_assessment', 'user_edit', 'ai_analysis'
    previous_version: str | None = None

    @property
    def event_type(self) -> str:
        return "metadata.updated"
