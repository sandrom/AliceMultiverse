"""Unified provider base class for AI generation services."""

import logging
import time
import random
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Callable
from functools import wraps

from ..events.postgres_events import publish_event
from .types import (
    CostEstimate,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderStatus,
)
from .health_monitor import health_monitor
from .generation_tracker import get_generation_tracker
from ..core.structured_logging import get_logger, trace_operation, CorrelationContext
from ..core.metrics import (
    api_requests_total,
    api_request_duration_seconds,
    api_request_cost_dollars,
    update_provider_health_metrics
)

logger = get_logger(__name__)

T = TypeVar('T')


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


class Provider(ABC):
    """Unified base class for AI generation providers.
    
    This class combines all provider functionality:
    - Core provider interface
    - Event publishing
    - Cost tracking and estimation
    - Request validation
    - Error handling
    - Retry logic with exponential backoff
    """
    
    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0  # seconds
    DEFAULT_MAX_DELAY = 30.0  # seconds
    DEFAULT_BACKOFF_FACTOR = 2.0
    DEFAULT_JITTER = 0.1  # 10% jitter

    def __init__(self, api_key: Optional[str] = None):
        """Initialize provider.
        
        Args:
            api_key: API key for authentication
        """
        self.api_key = api_key
        self._status = ProviderStatus.UNKNOWN
        self._last_check: Optional[datetime] = None
        self._total_cost = 0.0
        self._generation_count = 0
        
        # Retry configuration (can be overridden by subclasses)
        self.max_retries = self.DEFAULT_MAX_RETRIES
        self.initial_delay = self.DEFAULT_INITIAL_DELAY
        self.max_delay = self.DEFAULT_MAX_DELAY
        self.backoff_factor = self.DEFAULT_BACKOFF_FACTOR
        self.jitter = self.DEFAULT_JITTER

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

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content based on request with retry logic and health monitoring.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
            
        Raises:
            ProviderError: If generation fails
            BudgetExceededError: If request would exceed budget
        """
        # Check circuit breaker
        if not health_monitor.can_execute(self.name):
            error_msg = f"{self.name} is currently unavailable (circuit breaker open)"
            logger.error(
                error_msg,
                provider=self.name,
                circuit_breaker_state="open"
            )
            raise GenerationError(error_msg)
        
        start_time = time.time()
        
        try:
            # Validate request
            await self.validate_request(request)
            
            # Publish start event
            self._publish_started(request)
            
            # Perform generation with retry logic
            logger.info(
                "Starting generation",
                provider=self.name,
                model=request.model or "default",
                generation_type=request.generation_type.value,
                budget_limit=request.budget_limit
            )
            result = await self._retry_async(self._generate, request)
            
            # Track metrics
            result.generation_time = time.time() - start_time
            self._total_cost += result.cost or 0.0
            self._generation_count += 1
            
            # Record success with health monitor
            health_monitor.record_success(self.name, result.generation_time)
            
            # Track generation for reproducibility
            if result.file_path:
                tracker = get_generation_tracker()
                asset_id = await tracker.track_generation(request, result, self.name)
                if asset_id:
                    result.asset_id = asset_id
            
            # Update metrics
            api_requests_total.labels(
                provider=self.name,
                model=result.model or request.model or "default",
                operation=request.generation_type.value,
                status="success"
            ).inc()
            
            api_request_duration_seconds.labels(
                provider=self.name,
                model=result.model or request.model or "default",
                operation=request.generation_type.value
            ).observe(result.generation_time)
            
            if result.cost:
                api_request_cost_dollars.labels(
                    provider=self.name,
                    model=result.model or request.model or "default"
                ).observe(result.cost)
            
            # Log success
            logger.info(
                "Generation completed",
                provider=self.name,
                model=result.model or request.model or "default",
                generation_time=result.generation_time,
                cost=result.cost,
                success=True
            )
            
            # Publish success event
            self._publish_success(request, result)
            
            return result
            
        except Exception as e:
            # Record failure with health monitor
            health_monitor.record_failure(self.name)
            
            # Update metrics
            api_requests_total.labels(
                provider=self.name,
                model=request.model or "default",
                operation=request.generation_type.value,
                status="error"
            ).inc()
            
            # Log failure
            logger.error(
                "Generation failed",
                provider=self.name,
                model=request.model or "default",
                generation_type=request.generation_type.value,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            
            # Publish failure event
            self._publish_failure(request, str(e))
            raise

    @abstractmethod
    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Perform the actual generation (implemented by subclasses).
        
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
    
    def get_health_status(self) -> ProviderStatus:
        """Get provider health status from monitor.
        
        Returns:
            Provider status based on circuit breaker state
        """
        return health_monitor.get_status(self.name)
    
    def get_health_metrics(self) -> Optional[Dict[str, Any]]:
        """Get provider health metrics.
        
        Returns:
            Health metrics if available
        """
        metrics = health_monitor.get_metrics(self.name)
        if not metrics:
            return None
            
        return {
            "total_requests": metrics.total_requests,
            "failed_requests": metrics.failed_requests,
            "failure_rate": metrics.failure_rate,
            "consecutive_failures": metrics.consecutive_failures,
            "average_response_time": metrics.average_response_time,
            "last_success": metrics.last_success_time.isoformat() if metrics.last_success_time else None,
            "last_failure": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
            "is_healthy": metrics.is_healthy
        }

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
                model=request.model or self.get_default_model(request.generation_type),
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

    @property
    def total_cost(self) -> float:
        """Total cost of all generations."""
        return self._total_cost

    @property
    def generation_count(self) -> int:
        """Total number of generations."""
        return self._generation_count

    # Event publishing methods
    
    def _publish_started(self, request: GenerationRequest):
        """Publish generation started event."""
        publish_event(
            "generation.started",
            {
                "source": f"provider:{self.name}",
                "generation_type": request.generation_type.value,
                "provider": self.name,
                "model": request.model or "default",
                "prompt": request.prompt,
                "parameters": request.parameters or {},
            }
        )
    
    def _publish_success(self, request: GenerationRequest, result: GenerationResult):
        """Publish success event."""
        if result.file_path:
            publish_event(
                "asset.generated",
                {
                    "source": f"provider:{self.name}",
                    "asset_id": result.asset_id or "",
                    "file_path": str(result.file_path),
                    "generation_type": request.generation_type.value,
                    "provider": self.name,
                    "model": result.model or request.model or "default",
                    "prompt": request.prompt,
                    "parameters": request.parameters or {},
                    "cost": result.cost,
                    "generation_time": result.generation_time,
                }
            )

    def _publish_failure(self, request: GenerationRequest, error: str):
        """Publish failure event."""
        publish_event(
            "generation.failed",
            {
                "source": f"provider:{self.name}",
                "generation_type": request.generation_type.value,
                "provider": self.name,
                "model": request.model or "default",
                "prompt": request.prompt,
                "error": error,
                "parameters": request.parameters or {},
            }
        )

    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Subclasses should override to clean up resources
        pass
    
    # Retry logic methods
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(
            self.initial_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )
        # Add jitter to prevent thundering herd
        jitter_amount = delay * self.jitter
        delay += random.uniform(-jitter_amount, jitter_amount)
        return max(0, delay)
    
    def _should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry.
        
        Override this method in subclasses to customize retry logic.
        """
        # Don't retry validation errors or budget exceeded
        if isinstance(exception, (ValueError, BudgetExceededError, AuthenticationError)):
            return False
            
        # Retry rate limit errors with longer delay
        if isinstance(exception, RateLimitError):
            return True
            
        # Default: retry on common transient errors
        error_msg = str(exception).lower()
        transient_errors = [
            'timeout', 'timed out',
            'connection', 'network',
            'temporarily unavailable',
            'service unavailable',
            '502', '503', '504',  # Gateway errors
            'rate limit', 'too many requests',
            'internal server error', '500'
        ]
        return any(error in error_msg for error in transient_errors)
    
    async def _retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Retry an async function with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(
                        "Max retries exceeded",
                        provider=self.name,
                        attempts=self.max_retries + 1,
                        final_error=str(e),
                        error_type=type(e).__name__
                    )
                    raise
                
                if not self._should_retry(e):
                    logger.error(
                        "Non-retryable error",
                        provider=self.name,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                    raise
                
                # Special handling for rate limit errors
                if isinstance(e, RateLimitError):
                    # Use longer delay for rate limits
                    delay = self._calculate_delay(attempt + 2)  # Extra backoff
                else:
                    delay = self._calculate_delay(attempt)
                
                logger.warning(
                    "Retrying after failure",
                    provider=self.name,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1,
                    retry_delay=delay,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic error")
    
    def retry_with_backoff(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to retry a sync function with exponential backoff.
        
        For use with synchronous methods in providers.
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        logger.error(
                            f"{self.name}: Failed after {self.max_retries + 1} attempts: {e}"
                        )
                        raise
                    
                    if not self._should_retry(e):
                        logger.error(f"{self.name}: Non-retryable error: {e}")
                        raise
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"{self.name}: Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error")
        
        return wrapper