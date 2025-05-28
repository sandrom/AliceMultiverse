"""Provider registry for managing AI generation providers.

MIGRATION NOTE: This module now uses EnhancedProviderRegistry internally
for better cost tracking and provider management. The API remains compatible.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type

from ..events.base import EventBus
from .base import GenerationProvider, GenerationType
from .enhanced_registry import EnhancedProviderRegistry
from .anthropic_provider import AnthropicProvider
from .fal_provider import FalProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for managing generation providers.
    
    This is now a compatibility wrapper around EnhancedProviderRegistry.
    """

    # Available provider classes (for backward compatibility)
    PROVIDERS: Dict[str, Type[GenerationProvider]] = {
        "fal": FalProvider,
        "fal.ai": FalProvider,  # Alias
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,  # Alias
    }

    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize provider registry.
        
        Args:
            event_bus: Event bus for providers to use
        """
        # Use enhanced registry internally
        self._enhanced_registry = EnhancedProviderRegistry(event_bus)
        
        # Register existing providers
        for name, provider_class in self.PROVIDERS.items():
            self._enhanced_registry.register_provider(name, provider_class)
        
        # Legacy compatibility
        self.event_bus = event_bus or EventBus()
        self._instances: Dict[str, GenerationProvider] = {}
        self._api_keys: Dict[str, str] = {}

    def register_api_key(self, provider_name: str, api_key: str):
        """Register an API key for a provider.
        
        Args:
            provider_name: Provider name
            api_key: API key
        """
        self._api_keys[provider_name.lower()] = api_key
        self._enhanced_registry.register_api_key(provider_name, api_key)

    def get_provider(self, name: str) -> GenerationProvider:
        """Get a provider instance by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider not found
            RuntimeError: If called from async context (use get_provider_async instead)
        """
        # Check if we're in an async context
        try:
            asyncio.get_running_loop()
            # We're in an async context - this is unsafe
            raise RuntimeError(
                "get_provider() cannot be called from async context. "
                "Use 'await get_provider_async(name)' instead."
            )
        except RuntimeError:
            # No running loop - safe to proceed
            pass
        
        # Use async method synchronously for compatibility
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._enhanced_registry.get_provider(name))
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def get_providers_for_type(self, generation_type: GenerationType) -> List[str]:
        """Get providers that support a generation type.
        
        Args:
            generation_type: Type of generation
            
        Returns:
            List of provider names
        """
        return self._enhanced_registry.get_providers_for_type(generation_type)

    def list_providers(self) -> List[str]:
        """List all available providers.
        
        Returns:
            List of provider names
        """
        return self._enhanced_registry.list_providers()
    
    # New methods exposed from enhanced registry
    
    def get_stats(self, provider_name: Optional[str] = None) -> Dict[str, any]:
        """Get statistics for providers.
        
        Args:
            provider_name: Specific provider or None for all
            
        Returns:
            Statistics dictionary
        """
        return self._enhanced_registry.get_stats(provider_name)
    
    def set_budget_limit(self, limit: float):
        """Set global budget limit.
        
        Args:
            limit: Budget limit in USD
        """
        self._enhanced_registry.budget_limit = limit
    
    def disable_provider(self, provider_name: str):
        """Temporarily disable a provider.
        
        Args:
            provider_name: Provider to disable
        """
        self._enhanced_registry.disable_provider(provider_name)
    
    def enable_provider(self, provider_name: str):
        """Re-enable a disabled provider.
        
        Args:
            provider_name: Provider to enable
        """
        self._enhanced_registry.enable_provider(provider_name)
    
    # Async methods for use in async contexts
    
    async def get_provider_async(self, name: str) -> GenerationProvider:
        """Get a provider instance by name (async version).
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider not found
        """
        return await self._enhanced_registry.get_provider(name)
    
    async def select_provider_async(self, request) -> GenerationProvider:
        """Select best provider for request (async version).
        
        Args:
            request: Generation request
            
        Returns:
            Selected provider
        """
        return await self._enhanced_registry.select_provider(request)


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry(event_bus: Optional[EventBus] = None) -> ProviderRegistry:
    """Get global provider registry.
    
    Args:
        event_bus: Event bus to use (only on first call)
        
    Returns:
        Provider registry
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry(event_bus)
    return _registry


def get_provider(name: str, api_key: Optional[str] = None) -> GenerationProvider:
    """Convenience function to get a provider.
    
    Args:
        name: Provider name
        api_key: Optional API key to register
        
    Returns:
        Provider instance
    """
    registry = get_registry()
    
    if api_key:
        registry.register_api_key(name, api_key)
    
    return registry.get_provider(name)


# New convenience functions

def set_global_budget(limit: float):
    """Set global budget limit across all providers.
    
    Args:
        limit: Budget limit in USD
    """
    registry = get_registry()
    registry.set_budget_limit(limit)


def get_cost_report() -> Dict[str, any]:
    """Get cost report across all providers.
    
    Returns:
        Cost statistics
    """
    registry = get_registry()
    return registry.get_stats()


# Async convenience functions

async def get_provider_async(name: str, api_key: Optional[str] = None) -> GenerationProvider:
    """Async version of get_provider.
    
    Args:
        name: Provider name
        api_key: Optional API key to register
        
    Returns:
        Provider instance
    """
    registry = get_registry()
    
    if api_key:
        registry.register_api_key(name, api_key)
    
    return await registry.get_provider_async(name)