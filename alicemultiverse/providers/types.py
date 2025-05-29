"""Common types for provider implementations."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class GenerationType(str, Enum):
    """Types of content that can be generated."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"


class ProviderStatus(str, Enum):
    """Provider availability status."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class GenerationRequest:
    """Request to generate content."""
    prompt: str
    generation_type: GenerationType
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    reference_assets: Optional[List[str]] = None  # Asset IDs or URLs for reference images
    reference_weights: Optional[List[float]] = None  # Weights for multi-reference models
    output_format: Optional[str] = None  # png, jpg, mp4, etc.
    output_path: Optional[Path] = None  # Where to save the result
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata to embed
    project_id: Optional[str] = None  # For future project management
    budget_limit: Optional[float] = None  # Max cost for this generation


@dataclass
class GenerationResult:
    """Result of a generation operation."""
    success: bool
    asset_id: Optional[str] = None
    file_path: Optional[Path] = None
    generation_time: Optional[float] = None  # Seconds
    cost: Optional[float] = None  # USD
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    timestamp: datetime = None  # When generation completed
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ProviderCapabilities:
    """What a provider can do."""
    generation_types: List[GenerationType]
    models: List[str]
    max_resolution: Optional[Dict[str, int]] = None  # {"width": 1024, "height": 1024}
    formats: Optional[List[str]] = None
    features: Optional[List[str]] = None  # ["style_reference", "controlnet", etc.]
    rate_limits: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, float]] = None  # Cost per generation
    supports_streaming: bool = False  # For real-time generation
    supports_batch: bool = False  # For batch generation


@dataclass
class CostEstimate:
    """Cost estimate for a generation request."""
    provider: str
    model: str
    estimated_cost: float
    confidence: float = 1.0  # 0-1, how confident we are in the estimate
    breakdown: Optional[Dict[str, float]] = None  # Cost breakdown by component