"""Enhanced base provider interface for AI generation services."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List, Optional

from .event_mixin import ProviderEventMixin
from .types import (
    CostEstimate,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


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


class BudgetExceededError(ProviderError):
    """Raised when generation would exceed budget."""
    pass


class BaseProvider(ProviderEventMixin, ABC):
    """Abstract base class for AI generation providers."""

    def __init__(self, api_key: Optional[str] = None, event_bus: Optional[Any] = None):
        """Initialize provider.
        
        Args:
            api_key: API key for authentication
            event_bus: Deprecated parameter, kept for compatibility
        """
        self.api_key = api_key
        self.event_bus = None  # Deprecated
        self._status = ProviderStatus.UNKNOWN
        self._last_check: Optional[datetime] = None
        self._total_cost = 0.0  # Track total cost
        self._generation_count = 0  # Track number of generations

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
            BudgetExceededError: If request would exceed budget
        """
        pass

    @abstractmethod
    async def check_status(self) -> ProviderStatus:
        """Check provider availability.
        
        Returns:
            Provider status
        """
        pass

    async def estimate_cost(self, request: GenerationRequest) -> CostEstimate:
        """Estimate cost for a generation request.
        
        Args:
            request: Generation request
            
        Returns:
            Cost estimate with breakdown
        """
        if not self.capabilities.pricing:
            return CostEstimate(
                provider=self.name,
                model=request.model or "default",
                estimated_cost=0.0,
                confidence=1.0
            )
        
        # Get base price for model
        model = request.model or self.get_default_model(request.generation_type)
        base_price = self.capabilities.pricing.get(model, 0.0)
        
        # Calculate modifiers
        cost_breakdown = {"base": base_price}
        total_cost = base_price
        
        # Resolution modifier for images
        if request.generation_type == GenerationType.IMAGE and request.parameters:
            width = request.parameters.get("width", 1024)
            height = request.parameters.get("height", 1024)
            pixels = width * height
            base_pixels = 1024 * 1024
            
            if pixels != base_pixels:
                resolution_multiplier = pixels / base_pixels
                resolution_cost = base_price * (resolution_multiplier - 1)
                cost_breakdown["resolution"] = resolution_cost
                total_cost += resolution_cost
        
        # Duration modifier for video
        if request.generation_type == GenerationType.VIDEO and request.parameters:
            duration = request.parameters.get("duration", 5)
            if duration > 5:
                duration_cost = base_price * (duration / 5 - 1)
                cost_breakdown["duration"] = duration_cost
                total_cost += duration_cost
        
        return CostEstimate(
            provider=self.name,
            model=model,
            estimated_cost=total_cost,
            confidence=0.9,  # Estimates are usually close but not exact
            breakdown=cost_breakdown
        )

    async def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request.
        
        Args:
            request: Generation request
            
        Raises:
            ValueError: If request is invalid
            BudgetExceededError: If request would exceed budget
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
        
        # Check budget
        if request.budget_limit is not None:
            estimate = await self.estimate_cost(request)
            if estimate.estimated_cost > request.budget_limit:
                raise BudgetExceededError(
                    f"Estimated cost ${estimate.estimated_cost:.3f} exceeds "
                    f"budget limit ${request.budget_limit:.3f}"
                )
        
        # Check resolution limits for images
        if (request.generation_type == GenerationType.IMAGE and 
            request.parameters and 
            self.capabilities.max_resolution):
            
            width = request.parameters.get("width", 1024)
            height = request.parameters.get("height", 1024)
            max_width = self.capabilities.max_resolution.get("width", float("inf"))
            max_height = self.capabilities.max_resolution.get("height", float("inf"))
            
            if width > max_width or height > max_height:
                raise ValueError(
                    f"Resolution {width}x{height} exceeds maximum "
                    f"{max_width}x{max_height} for {self.name}"
                )

    def get_default_model(self, generation_type: GenerationType) -> str:
        """Get default model for a generation type.
        
        Args:
            generation_type: Type of generation
            
        Returns:
            Default model name
        """
        # Subclasses should override this for smarter defaults
        return self.capabilities.models[0] if self.capabilities.models else "default"

    @property
    def total_cost(self) -> float:
        """Total cost of all generations."""
        return self._total_cost

    @property
    def generation_count(self) -> int:
        """Total number of generations."""
        return self._generation_count

    def get_models_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get available models for a generation type.
        
        Args:
            generation_type: Type of generation
            
        Returns:
            List of model names
        """
        # Base implementation returns all models
        # Subclasses can override for type-specific filtering
        return self.capabilities.models

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Subclasses should override to clean up resources
        pass