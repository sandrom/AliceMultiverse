"""Data models for Asset Processor service."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from alice_models import MediaType, QualityRating, SourceType


class AnalyzeRequest(BaseModel):
    """Request to analyze an asset."""
    file_path: str = Field(description="Path to the media file")
    extract_ai_params: bool = Field(default=True, description="Extract AI generation parameters")
    extract_exif: bool = Field(default=True, description="Extract EXIF metadata")


class AnalyzeResponse(BaseModel):
    """Response from asset analysis."""
    content_hash: str = Field(description="SHA256 hash of file content")
    media_type: MediaType = Field(description="Type of media")
    file_size: int = Field(description="File size in bytes")
    
    # Detected AI source
    ai_source: Optional[SourceType] = Field(description="Detected AI generation source")
    
    # Basic metadata
    metadata: Dict[str, Any] = Field(description="General metadata")
    
    # Extracted metadata
    extracted_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted technical metadata (EXIF, etc.)"
    )
    
    # AI generation parameters
    generation_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="AI generation parameters if found"
    )
    
    # Semantic tags
    tags: List[str] = Field(default_factory=list, description="Semantic tags")
    
    # For images/video
    dimensions: Optional[Dict[str, int]] = Field(
        default=None,
        description="Width and height for images/video"
    )
    
    # Processing info
    processing_time_ms: int = Field(description="Processing time in milliseconds")


class QualityAssessRequest(BaseModel):
    """Request to assess quality."""
    file_path: str = Field(description="Path to the media file")
    content_hash: str = Field(description="Content hash for caching")
    pipeline_mode: str = Field(
        default="basic",
        description="Pipeline mode: basic, standard, premium"
    )
    force_reanalyze: bool = Field(
        default=False,
        description="Force re-analysis even if cached"
    )


class QualityAssessResponse(BaseModel):
    """Response from quality assessment."""
    star_rating: QualityRating = Field(description="Star rating (1-5)")
    combined_score: float = Field(description="Combined quality score (0-1)")
    
    # Individual scores
    brisque_score: Optional[float] = Field(
        default=None,
        description="BRISQUE score (0-100, lower is better)"
    )
    sightengine_score: Optional[float] = Field(
        default=None,
        description="SightEngine score (0-1, higher is better)"
    )
    claude_assessment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Claude's quality assessment"
    )
    
    # Quality issues
    quality_issues: List[str] = Field(
        default_factory=list,
        description="Detected quality issues"
    )
    
    # Pipeline info
    pipeline_mode: str = Field(description="Pipeline mode used")
    stages_completed: List[str] = Field(
        default_factory=list,
        description="Completed pipeline stages"
    )
    assessment_duration_ms: int = Field(description="Assessment time in milliseconds")


class OrganizePlanRequest(BaseModel):
    """Request to plan asset organization."""
    file_path: str = Field(description="Path to the media file")
    content_hash: str = Field(description="Content hash")
    metadata: Dict[str, Any] = Field(description="Asset metadata")
    quality_rating: Optional[QualityRating] = Field(
        default=None,
        description="Quality rating if assessed"
    )
    project_name: Optional[str] = Field(
        default=None,
        description="Project name override"
    )


class OrganizePlanResponse(BaseModel):
    """Response with organization plan."""
    destination_path: str = Field(description="Suggested destination path")
    
    # Path components
    date_folder: str = Field(description="Date folder (YYYY-MM-DD)")
    project_name: str = Field(description="Project name")
    source_type: str = Field(description="AI source type folder")
    quality_folder: Optional[str] = Field(
        default=None,
        description="Quality folder (e.g., '5-star')"
    )
    
    # File naming
    sequence_number: int = Field(description="Sequence number for file")
    suggested_filename: str = Field(description="Suggested filename")
    
    # Organization metadata
    organization_rule: str = Field(
        default="date-project-source",
        description="Organization rule applied"
    )
    preserve_original_name: bool = Field(
        default=False,
        description="Whether to preserve original filename"
    )


class BatchProcessRequest(BaseModel):
    """Request to process multiple files."""
    file_paths: List[str] = Field(description="List of file paths to process")
    pipeline_mode: str = Field(default="basic", description="Quality pipeline mode")
    skip_quality: bool = Field(default=False, description="Skip quality assessment")


class BatchProcessResponse(BaseModel):
    """Response from batch processing."""
    total_files: int = Field(description="Total files processed")
    successful: int = Field(description="Successfully processed files")
    failed: int = Field(description="Failed files")
    results: List[Dict[str, Any]] = Field(description="Individual file results")