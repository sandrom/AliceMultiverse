"""Common types for provider implementations."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


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
    model: str | None = None
    parameters: dict[str, Any] | None = None
    reference_assets: list[str] | None = None  # Asset IDs or URLs for reference images
    output_format: str | None = None  # png, jpg, mp4, etc.
    output_path: Path | None = None  # Where to save the result
    metadata: dict[str, Any] | None = None  # Additional metadata to embed
    budget_limit: float | None = None  # Max cost for this generation


@dataclass
class GenerationResult:
    """Result of a generation operation."""
    success: bool
    file_path: Path | None = None
    generation_time: float | None = None  # Seconds
    cost: float | None = None  # USD
    metadata: dict[str, Any] | None = None
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    timestamp: datetime = None  # When generation completed

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ProviderCapabilities:
    """What a provider can do."""
    generation_types: list[GenerationType]
    models: list[str]
    max_resolution: dict[str, int] | None = None  # {"width": 1024, "height": 1024}
    formats: list[str] | None = None
    features: list[str] | None = None  # ["style_reference", "controlnet", etc.]
    rate_limits: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None  # Cost per generation or model


@dataclass
class CostEstimate:
    """Cost estimate for a generation request."""
    provider: str
    model: str
    estimated_cost: float
