"""Core data models for AliceMultiverse."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from .enums import MediaType, QualityRating, WorkflowState, ProcessingStatus, SourceType
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
    source_type: Optional[SourceType] = None
    quality_rating: Optional[QualityRating] = None
    processing_status: ProcessingStatus = ProcessingStatus.UNPROCESSED
    metadata: Dict[str, Any] = field(default_factory=dict)
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
    style_preferences: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    parent_project_id: Optional[ProjectId] = None
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
    project_id: Optional[ProjectId] = None
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Progress
    current_step: Optional[str] = None
    total_steps: int = 0
    completed_steps: int = 0
    
    @property
    def duration_seconds(self) -> Optional[float]:
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
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    format: Optional[str] = None
    codec: Optional[str] = None
    
    # EXIF/Technical metadata
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens: Optional[str] = None
    focal_length: Optional[float] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    
    # AI generation metadata
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    model_name: Optional[str] = None
    model_hash: Optional[str] = None
    sampler: Optional[str] = None
    cfg_scale: Optional[float] = None
    steps: Optional[int] = None
    seed: Optional[int] = None
    
    # Custom metadata
    custom: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None