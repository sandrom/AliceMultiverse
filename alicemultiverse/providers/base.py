"""Base provider interface for AI generation services."""

import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..events.base import EventBus

logger = logging.getLogger(__name__)


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


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""
    pass


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""
    pass


class GenerationError(ProviderError):
    """Raised when generation fails."""
    pass


@dataclass
class GenerationRequest:
    """Request to generate content."""
    prompt: str
    generation_type: GenerationType
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    reference_assets: Optional[List[str]] = None  # Asset IDs for style reference
    output_format: Optional[str] = None  # png, jpg, mp4, etc.
    output_path: Optional[Path] = None  # Where to save the result
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata to embed


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


class GenerationProvider(ABC):
    """Abstract base class for AI generation providers."""

    def __init__(self, api_key: Optional[str] = None, event_bus: Optional[EventBus] = None):
        """Initialize provider.
        
        Args:
            api_key: API key for authentication
            event_bus: Event bus for publishing events
        """
        self.api_key = api_key
        self.event_bus = event_bus or EventBus()
        self._status = ProviderStatus.UNKNOWN
        self._last_check = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Provider capabilities."""
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content based on request.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
            
        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def check_status(self) -> ProviderStatus:
        """Check provider availability.
        
        Returns:
            Provider status
        """
        pass

    async def estimate_cost(self, request: GenerationRequest) -> float:
        """Estimate cost for a generation request.
        
        Args:
            request: Generation request
            
        Returns:
            Estimated cost in USD
        """
        if not self.capabilities.pricing:
            return 0.0
        
        # Default implementation - providers can override
        base_price = self.capabilities.pricing.get(request.generation_type.value, 0.0)
        
        # Adjust for resolution if applicable
        if request.parameters and request.generation_type == GenerationType.IMAGE:
            width = request.parameters.get("width", 512)
            height = request.parameters.get("height", 512)
            pixels = width * height
            base_pixels = 512 * 512
            if pixels > base_pixels:
                base_price *= (pixels / base_pixels)
        
        return base_price

    async def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request.
        
        Args:
            request: Generation request
            
        Raises:
            ValueError: If request is invalid
        """
        # Check generation type
        if request.generation_type not in self.capabilities.generation_types:
            raise ValueError(
                f"{self.name} does not support {request.generation_type} generation"
            )
        
        # Check model if specified
        if request.model and request.model not in self.capabilities.models:
            raise ValueError(
                f"Model '{request.model}' not available. "
                f"Available models: {', '.join(self.capabilities.models)}"
            )
        
        # Check resolution limits for images
        if (request.generation_type == GenerationType.IMAGE and 
            request.parameters and 
            self.capabilities.max_resolution):
            
            width = request.parameters.get("width", 512)
            height = request.parameters.get("height", 512)
            max_width = self.capabilities.max_resolution.get("width", float("inf"))
            max_height = self.capabilities.max_resolution.get("height", float("inf"))
            
            if width > max_width or height > max_height:
                raise ValueError(
                    f"Resolution {width}x{height} exceeds maximum "
                    f"{max_width}x{max_height} for {self.name}"
                )

    def _publish_success(self, request: GenerationRequest, result: GenerationResult):
        """Publish success event."""
        if self.event_bus and result.file_path:
            # Import here to avoid circular dependencies
            from ..events.asset_events import AssetGeneratedEvent
            from ..events.base import create_event
            
            event = create_event(
                AssetGeneratedEvent,
                source=f"provider:{self.name}",
                asset_id=result.asset_id or "",
                file_path=str(result.file_path),
                generation_type=request.generation_type.value,
                provider=self.name,
                model=result.model or request.model or "default",
                prompt=request.prompt,
                parameters=request.parameters or {},
                cost=result.cost,
                generation_time=result.generation_time,
            )
            self._sync_publish(event)

    def _publish_failure(self, request: GenerationRequest, error: str):
        """Publish failure event."""
        if self.event_bus:
            # Import here to avoid circular dependencies
            from ..events.asset_events import GenerationFailedEvent
            from ..events.base import create_event
            
            event = create_event(
                GenerationFailedEvent,
                source=f"provider:{self.name}",
                generation_type=request.generation_type.value,
                provider=self.name,
                model=request.model or "default",
                prompt=request.prompt,
                error=error,
                parameters=request.parameters or {},
            )
            self._sync_publish(event)
    
    def _sync_publish(self, event):
        """Publish event synchronously."""
        # Check if we have an event loop running
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            asyncio.create_task(self.event_bus.publish(event))
        except RuntimeError:
            # No event loop, run sync
            asyncio.run(self.event_bus.publish(event))