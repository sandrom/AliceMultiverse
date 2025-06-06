"""Data models for prompt management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


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
    output_path: Optional[str] = None
    cost: Optional[float] = None
    duration_seconds: Optional[float] = None
    notes: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptVariation:
    """A variation of a base prompt."""
    id: str
    parent_id: str
    variation_text: str
    differences: str  # What changed from parent
    purpose: str  # Why this variation exists
    effectiveness_rating: Optional[float] = None  # 0-10
    use_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class Prompt:
    """Main prompt entity."""
    id: str
    text: str
    category: PromptCategory
    providers: List[ProviderType]  # Which providers this works well with
    
    # Organization
    tags: List[str] = field(default_factory=list)
    project: Optional[str] = None
    style: Optional[str] = None  # e.g., "cyberpunk", "minimalist"
    
    # Effectiveness tracking
    effectiveness_rating: Optional[float] = None  # 0-10 overall rating
    use_count: int = 0
    success_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Descriptive fields
    description: Optional[str] = None  # What this prompt is good for
    notes: Optional[str] = None  # Additional notes, tips, warnings
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)  # e.g., {"aspect_ratio": "16:9", "model": "v6"}
    
    # Related prompts
    parent_id: Optional[str] = None  # If this is derived from another prompt
    related_ids: List[str] = field(default_factory=list)  # Similar or complementary prompts
    
    # Search helpers
    keywords: List[str] = field(default_factory=list)  # Additional search terms
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.use_count == 0:
            return 0.0
        return self.success_count / self.use_count
    
    def add_usage(self, usage: PromptUsage) -> None:
        """Update stats based on usage."""
        self.use_count += 1
        if usage.success:
            self.success_count += 1
        self.updated_at = datetime.now()


@dataclass
class PromptSearchCriteria:
    """Criteria for searching prompts."""
    query: Optional[str] = None  # Text search in prompt, description, notes
    category: Optional[PromptCategory] = None
    providers: Optional[List[ProviderType]] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None
    style: Optional[str] = None
    min_effectiveness: Optional[float] = None
    min_success_rate: Optional[float] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_variations: Optional[bool] = None
    keywords: Optional[List[str]] = None