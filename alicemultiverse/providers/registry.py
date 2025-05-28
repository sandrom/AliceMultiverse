"""Provider registry for managing AI generation providers.

This module provides a simplified registry for provider management.
"""

# Re-export everything from simple_registry for backward compatibility
from .simple_registry import (
    ProviderRegistry,
    ProviderStats,
    get_provider,
    get_provider_async,
    get_registry,
)

__all__ = [
    "ProviderRegistry",
    "ProviderStats", 
    "get_provider",
    "get_provider_async",
    "get_registry",
]