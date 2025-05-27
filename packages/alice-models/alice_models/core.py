"""Core data models for AliceMultiverse."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .enums import MediaType, ProcessingStatus, QualityRating, SourceType, WorkflowState
from .types import ContentHash, FilePath, ProjectId, WorkflowId


@dataclass
class Asset:
    """Represents a media asset in the system."""

    content_hash: ContentHash
    file_path: FilePath
    media_type: MediaType
    file_size: int
    project_name: str

    # Optional fields
    source_type: SourceType | None = None
    quality_rating: QualityRating | None = None
    processing_status: ProcessingStatus = ProcessingStatus.UNPROCESSED
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Computed properties
    @property
    def file_name(self) -> str:
        """Get the filename from path."""
        return Path(self.file_path).name

    @property
    def file_extension(self) -> str:
        """Get the file extension."""
        return Path(self.file_path).suffix.lower()


@dataclass
class Project:
    """Represents a creative project."""

    id: ProjectId
    name: str
    description: str

    # Optional fields
    style_preferences: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    parent_project_id: ProjectId | None = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Stats
    asset_count: int = 0
    total_size_bytes: int = 0


@dataclass
class Workflow:
    """Represents a workflow execution."""

    id: WorkflowId
    workflow_type: str
    state: WorkflowState

    # Optional fields
    project_id: ProjectId | None = None
    input_parameters: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Progress
    current_step: str | None = None
    total_steps: int = 0
    completed_steps: int = 0

    @property
    def duration_seconds(self) -> float | None:
        """Calculate workflow duration."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage."""
        if self.total_steps > 0:
            return (self.completed_steps / self.total_steps) * 100
        return 0.0


@dataclass
class MediaMetadata:
    """Extracted metadata from media files."""

    content_hash: ContentHash

    # Common metadata
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    format: str | None = None
    codec: str | None = None

    # EXIF/Technical metadata
    camera_make: str | None = None
    camera_model: str | None = None
    lens: str | None = None
    focal_length: float | None = None
    aperture: float | None = None
    shutter_speed: str | None = None
    iso: int | None = None

    # AI generation metadata
    prompt: str | None = None
    negative_prompt: str | None = None
    model_name: str | None = None
    model_hash: str | None = None
    sampler: str | None = None
    cfg_scale: float | None = None
    steps: int | None = None
    seed: int | None = None

    # Custom metadata
    custom: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime | None = None
    modified_at: datetime | None = None
