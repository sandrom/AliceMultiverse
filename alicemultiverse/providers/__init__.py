"""Provider interfaces for AI generation services."""

# Re-export from base for backward compatibility
from .base import (
    GenerationProvider,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    ProviderCapabilities,
    ProviderError,
    ProviderStatus,
    RateLimitError,
    AuthenticationError,
    GenerationError,
)

# New base provider and types
from .base_provider import (
    BaseProvider,
    BudgetExceededError,
)
from .types import CostEstimate

# Implementations
from .fal_provider import FalProvider
from .registry import ProviderRegistry, get_provider, get_cost_report, set_global_budget

__all__ = [
    # Base classes and types (backward compatibility)
    "GenerationProvider",
    "GenerationRequest",
    "GenerationResult",
    "GenerationType",
    "ProviderCapabilities",
    "ProviderStatus",
    # New base provider
    "BaseProvider",
    # Errors
    "ProviderError",
    "RateLimitError",
    "AuthenticationError", 
    "GenerationError",
    "BudgetExceededError",
    # Types
    "CostEstimate",
    # Implementations
    "FalProvider",
    "ProviderRegistry",
    "get_provider",
    "get_cost_report",
    "set_global_budget",
]