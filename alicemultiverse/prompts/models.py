"""Data models for prompt management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PromptCategory(Enum):
    """Categories for organizing prompts."""
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    MUSIC_GENERATION = "music_generation"
    TEXT_GENERATION = "text_generation"
    STYLE_TRANSFER = "style_transfer"
    ENHANCEMENT = "enhancement"
    ANALYSIS = "analysis"
    OTHER = "other"


class ProviderType(Enum):
    """Supported AI providers."""
    MIDJOURNEY = "midjourney"
    DALLE = "dalle"
    STABLE_DIFFUSION = "stable_diffusion"
    FLUX = "flux"
    IDEOGRAM = "ideogram"
    LEONARDO = "leonardo"
    FIREFLY = "firefly"
    KLING = "kling"
    RUNWAY = "runway"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"
    OTHER = "other"


@dataclass
class PromptUsage:
    """Track individual usage of a prompt."""
    id: str
    prompt_id: str
    provider: ProviderType
    timestamp: datetime
    success: bool
    output_path: str | None = None
    cost: float | None = None
    duration_seconds: float | None = None
    notes: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptVariation:
    """A variation of a base prompt."""
    id: str
    parent_id: str
    variation_text: str
    differences: str  # What changed from parent
    purpose: str  # Why this variation exists
    effectiveness_rating: float | None = None  # 0-10
    use_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)


@dataclass
class Prompt:
    """Main prompt entity."""
    id: str
    text: str
    category: PromptCategory
    providers: list[ProviderType]  # Which providers this works well with

    # Organization
    tags: list[str] = field(default_factory=list)
    project: str | None = None
    style: str | None = None  # e.g., "cyberpunk", "minimalist"

    # Effectiveness tracking
    effectiveness_rating: float | None = None  # 0-10 overall rating
    use_count: int = 0
    success_count: int = 0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Descriptive fields
    description: str | None = None  # What this prompt is good for
    notes: str | None = None  # Additional notes, tips, warnings

    # Context
    context: dict[str, Any] = field(default_factory=dict)  # e.g., {"aspect_ratio": "16:9", "model": "v6"}

    # Related prompts
    parent_id: str | None = None  # If this is derived from another prompt
    related_ids: list[str] = field(default_factory=list)  # Similar or complementary prompts

    # Search helpers
    keywords: list[str] = field(default_factory=list)  # Additional search terms

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.use_count == 0:
            return 0.0
        # TODO: Review unreachable code - return float(self.success_count) / self.use_count

    def add_usage(self, usage: PromptUsage) -> None:
        """Update stats based on usage."""
        self.use_count += 1
        if usage.success:
            self.success_count += 1
        self.updated_at = datetime.now()


@dataclass
class PromptSearchCriteria:
    """Criteria for searching prompts."""
    query: str | None = None  # Text search in prompt, description, notes
    category: PromptCategory | None = None
    providers: list[ProviderType] | None = None
    tags: list[str] | None = None
    project: str | None = None
    style: str | None = None
    min_effectiveness: float | None = None
    min_success_rate: float | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    has_variations: bool | None = None
    keywords: list[str] | None = None
